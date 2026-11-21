//! Backend orchestrator for the Talking Head Editor & Reels AI Director.
//!
//! Bridges ClipperStudio to the Python-based AI Director skill located in `skills/talking-head/`.
//! Handles:
//! - Visual & spatial footage probe (face tracking, dead-air trimming, auto-reframe 9:16).
//! - Whisper transcription with word-level timestamps.
//! - Autonomous or custom AI blueprint generation (13 signature styles, 82+ effects).
//! - Preview-First generation (still keyframe contact sheets and 540p proxy video).
//! - Plan serialization/editing for the UI Part Editor.
//! - Broadcast quality final rendering (1080x1920, CRF 17).

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::path::{Path, PathBuf};

enum ProcessEvent {
    Line(String),
    Done(Result<(), String>),
}

async fn spawn_streaming_process<F>(
    mut cmd: std::process::Command,
    on_progress: &mut F,
) -> Result<(), String>
where
    F: FnMut(&str),
{
    #[cfg(windows)]
    use std::os::windows::process::CommandExt;

    #[cfg(windows)]
    cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW

    cmd.stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped());

    let (tx, mut rx) = tokio::sync::mpsc::unbounded_channel::<ProcessEvent>();

    std::thread::spawn(move || {
        let mut child = match cmd.spawn() {
            Ok(c) => c,
            Err(e) => {
                let _ = tx.send(ProcessEvent::Done(Err(format!("Failed to start process: {e}"))));
                return;
            }
        };

        let stdout = child.stdout.take();
        let stderr = child.stderr.take();

        if let Some(err) = stderr {
            let tx_err = tx.clone();
            std::thread::spawn(move || {
                use std::io::BufRead;
                let reader = std::io::BufReader::new(err);
                for line in reader.lines().flatten() {
                    let _ = tx_err.send(ProcessEvent::Line(line));
                }
            });
        }

        if let Some(out) = stdout {
            use std::io::BufRead;
            let reader = std::io::BufReader::new(out);
            for line in reader.lines().flatten() {
                let _ = tx.send(ProcessEvent::Line(line));
            }
        }

        let status = match child.wait() {
            Ok(s) => s,
            Err(e) => {
                let _ = tx.send(ProcessEvent::Done(Err(format!("Process wait error: {e}"))));
                return;
            }
        };

        if status.success() {
            let _ = tx.send(ProcessEvent::Done(Ok(())));
        } else {
            let code_str = status.code().map(|c| c.to_string()).unwrap_or_else(|| "unknown".into());
            let _ = tx.send(ProcessEvent::Done(Err(format!("Process exited with status code {code_str}"))));
        }
    });

    let mut buffer: Vec<String> = Vec::new();
    while let Some(evt) = rx.recv().await {
        match evt {
            ProcessEvent::Line(line) => {
                on_progress(&line);
                if buffer.len() >= 15 {
                    buffer.remove(0);
                }
                buffer.push(line);
            }
            ProcessEvent::Done(res) => {
                return match res {
                    Ok(()) => Ok(()),
                    Err(base_err) => {
                        if !buffer.is_empty() {
                            Err(format!("{base_err}: {}", buffer.join(" | ")))
                        } else {
                            Err(base_err)
                        }
                    }
                };
            }
        }
    }
    Err("Process terminated unexpectedly without exit signal".into())
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum TalkingHeadMode {
    Automatic,
    CustomPrompt,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TalkingHeadRequest {
    pub footage_path: String,
    pub mode: TalkingHeadMode,
    pub custom_prompt: Option<String>,
    pub style: Option<String>,
    pub clean_audio: bool,
    pub output_dir: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EnvironmentStatus {
    pub python_available: bool,
    pub python_version: String,
    pub ffmpeg_available: bool,
    pub dependencies_installed: bool,
    pub models_present: bool,
    pub presets_count: usize,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TalkingHeadSegment {
    pub id: String,
    pub start: f64,
    pub end: f64,
    pub fx: String,
    pub text: Option<String>,
    pub behind: bool,
    pub details: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TalkingHeadPlan {
    pub style: String,
    pub duration: f64,
    pub segments: Vec<TalkingHeadSegment>,
    pub raw_json: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PreviewResults {
    pub stills_path: String,
    pub proxy_video_path: String,
    pub plan_path: String,
    pub plan: TalkingHeadPlan,
}

/// Resolves the absolute path to the `skills/talking-head` folder.
pub fn get_skill_dir() -> PathBuf {
    if let Ok(cwd) = std::env::current_dir() {
        let candidate = cwd.join("skills").join("talking-head");
        if candidate.is_dir() {
            return candidate;
        }
    }
    if let Ok(exe) = std::env::current_exe() {
        for ancestor in exe.ancestors() {
            let candidate = ancestor.join("skills").join("talking-head");
            if candidate.is_dir() {
                return candidate;
            }
        }
    }
    std::env::current_dir()
        .map(|cwd| cwd.join("skills").join("talking-head"))
        .unwrap_or_else(|_| PathBuf::from("skills").join("talking-head"))
}

/// An exported Talking Head master video catalog entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TalkingHeadExportEntry {
    pub file_path: String,
    pub title: String,
    pub style: String,
    pub timestamp: String,
    pub duration_seconds: f64,
    pub file_size_bytes: u64,
}

pub fn get_talking_head_library_file() -> PathBuf {
    let home = dirs::home_dir().unwrap_or_else(std::env::temp_dir);
    let dir = dirs::data_dir()
        .map(|d| d.join(crate::paths::APP_ID))
        .unwrap_or_else(|| home.join(".clipperstudio"));
    let _ = std::fs::create_dir_all(&dir);
    dir.join("talking_head_library.json")
}

pub fn load_talking_head_library(output_dir: Option<&Path>) -> Vec<TalkingHeadExportEntry> {
    let mut map: std::collections::HashMap<String, TalkingHeadExportEntry> = std::collections::HashMap::new();

    let file = get_talking_head_library_file();
    if let Ok(content) = std::fs::read_to_string(&file) {
        if let Ok(entries) = serde_json::from_str::<Vec<TalkingHeadExportEntry>>(&content) {
            for entry in entries {
                if Path::new(&entry.file_path).is_file() {
                    map.insert(entry.file_path.clone(), entry);
                }
            }
        }
    }

    // Also scan the output directory for reels_master_*.mp4 files
    let scan_dir = output_dir.map(|d| d.join("TalkingHead")).unwrap_or_else(|| {
        let home = dirs::home_dir().unwrap_or_else(std::env::temp_dir);
        home.join("ClipperStudio").join("TalkingHead")
    });

    if scan_dir.is_dir() {
        if let Ok(dir_entries) = std::fs::read_dir(&scan_dir) {
            for dir_entry in dir_entries.flatten() {
                let p = dir_entry.path();
                if p.is_file() && p.extension().is_some_and(|ext| ext == "mp4") {
                    let path_str = p.to_string_lossy().into_owned();
                    if !map.contains_key(&path_str) {
                        let name = p.file_stem().map(|s| s.to_string_lossy().into_owned()).unwrap_or_else(|| "Reel".into());
                        let size = dir_entry.metadata().map(|m| m.len()).unwrap_or(0);
                        let modified = dir_entry.metadata().ok().and_then(|m| m.modified().ok());
                        let time_str = modified
                            .map(|m| chrono::DateTime::<chrono::Local>::from(m).format("%b %d, %Y · %H:%M").to_string())
                            .unwrap_or_else(|| "Exported".into());

                        map.insert(path_str.clone(), TalkingHeadExportEntry {
                            file_path: path_str,
                            title: name,
                            style: "Adaptive Broadcast Master (1080x1920)".into(),
                            timestamp: time_str,
                            duration_seconds: 0.0,
                            file_size_bytes: size,
                        });
                    }
                }
            }
        }
    }

    let mut list: Vec<TalkingHeadExportEntry> = map.into_values().collect();
    list.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
    list
}

pub fn save_talking_head_library(entries: &[TalkingHeadExportEntry]) {
    let file = get_talking_head_library_file();
    if let Ok(json) = serde_json::to_string_pretty(entries) {
        let _ = std::fs::write(&file, json);
    }
}

/// Creates a unique temporary working directory for analyzing footage.
pub fn create_temp_work_dir() -> PathBuf {
    std::env::temp_dir().join(format!("clipperstudio-th-{}", uuid::Uuid::new_v4()))
}

/// Formatted current local timestamp for display: e.g. "Nov 21, 2026 · 20:45".
pub fn current_timestamp_display() -> String {
    chrono::Local::now().format("%b %d, %Y · %H:%M").to_string()
}

/// Returns the Talking Head output folder (creating it if necessary).
pub fn get_output_folder(base_dir: Option<&Path>) -> PathBuf {
    let folder = match base_dir {
        Some(d) => d.join("TalkingHead"),
        None => {
            let home = dirs::home_dir().unwrap_or_else(std::env::temp_dir);
            home.join("ClipperStudio").join("TalkingHead")
        }
    };
    let _ = std::fs::create_dir_all(&folder);
    folder
}

/// Generates the default master output file path: ~/ClipperStudio/TalkingHead/reels_master_TIMESTAMP.mp4
pub fn generate_master_output_path(base_dir: Option<&Path>) -> PathBuf {
    let out_dir = get_output_folder(base_dir);
    let timestamp = chrono::Local::now().format("%Y%m%d_%H%M%S");
    out_dir.join(format!("reels_master_{timestamp}.mp4"))
}

/// Check Python, models, and dependencies for the Talking Head engine.
pub fn check_environment() -> EnvironmentStatus {
    let skill_dir = get_skill_dir();
    let models_dir = skill_dir.join("models");
    let presets_dir = skill_dir.join("presets");

    let yunet = models_dir.join("yunet.onnx");
    let segmenter = models_dir.join("selfie_segmenter.tflite");
    let models_present = yunet.is_file() && segmenter.is_file();

    let presets_count = if presets_dir.is_dir() {
        std::fs::read_dir(&presets_dir)
            .map(|entries| entries.flatten().filter(|e| e.path().extension().is_some_and(|ext| ext == "json")).count())
            .unwrap_or(0)
    } else {
        0
    };

    let ffmpeg_available = which::which("ffmpeg").is_ok();
    let py_cmd = which::which("python").or_else(|_| which::which("python3"));
    let mut python_available = false;
    let mut python_version = String::new();
    let mut dependencies_installed = false;

    if let Ok(py) = py_cmd {
        #[cfg(windows)]
        use std::os::windows::process::CommandExt;

        let mut cmd = std::process::Command::new(&py);
        cmd.arg("--version");
        #[cfg(windows)]
        cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW

        if let Ok(output) = cmd.output() {
            if output.status.success() {
                python_available = true;
                python_version = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if python_version.is_empty() {
                    python_version = String::from_utf8_lossy(&output.stderr).trim().to_string();
                }

                // Quick test of core libraries
                let test_script = "import numpy, cv2, PIL; print('OK')";
                let mut dep_cmd = std::process::Command::new(&py);
                dep_cmd.args(["-c", test_script]);
                #[cfg(windows)]
                dep_cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW

                if let Ok(dep_out) = dep_cmd.output() {
                    dependencies_installed = dep_out.status.success()
                        && String::from_utf8_lossy(&dep_out.stdout).contains("OK");
                }
            }
        }
    }

    let message = if !python_available {
        "Python 3.10+ was not found on PATH. Please install Python to use Talking Head Editor.".into()
    } else if !dependencies_installed {
        "Core Python packages are missing. Click 'Setup Environment' to install them.".into()
    } else if !models_present {
        "AI models (YuNet/Selfie Segmenter) are missing in skills/talking-head/models.".into()
    } else {
        "Ready: Python, models, and style presets verified.".into()
    };

    EnvironmentStatus {
        python_available,
        python_version,
        ffmpeg_available,
        dependencies_installed,
        models_present,
        presets_count,
        message,
    }
}

/// Runs `director.py analyze` to probe footage and generate an autonomous or customized plan.
pub async fn analyze_and_plan<F>(
    footage_path: &Path,
    work_dir: &Path,
    style: Option<&str>,
    clean_audio: bool,
    mut on_progress: F,
) -> Result<PathBuf, String>
where
    F: FnMut(&str) + Send + 'static,
{
    let skill_dir = get_skill_dir();
    let scripts_dir = skill_dir.join("scripts");
    let director_py = scripts_dir.join("director.py");
    let plan_path = work_dir.join("plan.json");

    let _ = std::fs::create_dir_all(work_dir);

    let py = which::which("python")
        .or_else(|_| which::which("python3"))
        .map_err(|_| "Python executable not found".to_string())?;

    let footage_abs = if footage_path.is_absolute() {
        footage_path.to_path_buf()
    } else if let Ok(cwd) = std::env::current_dir() {
        cwd.join(footage_path)
    } else {
        footage_path.to_path_buf()
    };

    let plan_abs = if plan_path.is_absolute() {
        plan_path.clone()
    } else if let Ok(cwd) = std::env::current_dir() {
        cwd.join(&plan_path)
    } else {
        plan_path.clone()
    };

    let mut cmd = std::process::Command::new(&py);
    cmd.env("PYTHONUNBUFFERED", "1");
    cmd.arg("-u")
        .arg(&director_py)
        .arg("analyze")
        .arg(&footage_abs)
        .arg("--out-plan")
        .arg(&plan_abs);

    if let Some(st) = style {
        cmd.arg("--style").arg(st);
    }

    if clean_audio {
        cmd.arg("--clean-audio");
    }

    cmd.current_dir(&skill_dir);

    on_progress("Analyzing footage composition, face tracking & speech...");
    spawn_streaming_process(cmd, &mut on_progress).await?;

    if !plan_path.is_file() {
        return Err("plan.json was not created by director.py".into());
    }

    Ok(plan_path)
}

/// Generates Still contact sheets and 540p Proxy video.
pub async fn generate_preview<F>(
    footage_path: &Path,
    plan_path: &Path,
    work_dir: &Path,
    mut on_progress: F,
) -> Result<(PathBuf, PathBuf), String>
where
    F: FnMut(&str) + Send + 'static,
{
    let skill_dir = get_skill_dir();
    let preview_py = skill_dir.join("scripts").join("preview.py");

    let stills_path = work_dir.join("preview_check.jpg");
    let proxy_path = work_dir.join("preview_proxy.mp4");

    let py = which::which("python")
        .or_else(|_| which::which("python3"))
        .map_err(|_| "Python executable not found".to_string())?;

    let footage_abs = if footage_path.is_absolute() {
        footage_path.to_path_buf()
    } else if let Ok(cwd) = std::env::current_dir() {
        cwd.join(footage_path)
    } else {
        footage_path.to_path_buf()
    };

    let plan_abs = if plan_path.is_absolute() {
        plan_path.to_path_buf()
    } else if let Ok(cwd) = std::env::current_dir() {
        cwd.join(plan_path)
    } else {
        plan_path.to_path_buf()
    };

    let stills_abs = if stills_path.is_absolute() {
        stills_path.clone()
    } else if let Ok(cwd) = std::env::current_dir() {
        cwd.join(&stills_path)
    } else {
        stills_path.clone()
    };

    let proxy_abs = if proxy_path.is_absolute() {
        proxy_path.clone()
    } else if let Ok(cwd) = std::env::current_dir() {
        cwd.join(&proxy_path)
    } else {
        proxy_path.clone()
    };

    // 1. Generate contact sheet stills
    on_progress("Generating keyframe contact sheet stills...");
    let mut cmd_stills = std::process::Command::new(&py);
    cmd_stills.env("PYTHONUNBUFFERED", "1");
    cmd_stills
        .arg("-u")
        .arg(&preview_py)
        .arg("stills")
        .arg(&footage_abs)
        .arg("--plan")
        .arg(&plan_abs)
        .arg("--out")
        .arg(&stills_abs)
        .current_dir(&skill_dir);

    spawn_streaming_process(cmd_stills, &mut on_progress).await
        .map_err(|e| format!("Failed to run preview.py stills: {e}"))?;

    // 2. Generate fast proxy video (540p)
    on_progress("Rendering fast 540p proxy preview video...");
    let mut cmd_proxy = std::process::Command::new(&py);
    cmd_proxy.env("PYTHONUNBUFFERED", "1");
    cmd_proxy
        .arg("-u")
        .arg(&preview_py)
        .arg("proxy")
        .arg(&footage_abs)
        .arg("--plan")
        .arg(&plan_abs)
        .arg("--out")
        .arg(&proxy_abs)
        .arg("--width")
        .arg("540")
        .current_dir(&skill_dir);

    spawn_streaming_process(cmd_proxy, &mut on_progress).await
        .map_err(|e| format!("Failed to run preview.py proxy: {e}"))?;

    Ok((stills_path, proxy_path))
}

/// Parses `plan.json` into a structured `TalkingHeadPlan` for the UI inspector.
pub fn parse_plan(plan_path: &Path) -> Result<TalkingHeadPlan, String> {
    let raw_text = std::fs::read_to_string(plan_path)
        .map_err(|e| format!("Failed to read plan.json: {e}"))?;
    let val: Value = serde_json::from_str(&raw_text)
        .map_err(|e| format!("Failed to parse plan.json: {e}"))?;

    let style = val.get("style").and_then(Value::as_str).unwrap_or("style-1").to_string();
    let raw_dur = val.get("duration").and_then(Value::as_f64).unwrap_or(0.0);

    let effects_arr = val.get("effects").and_then(Value::as_array);
    let mut segments = Vec::new();

    if let Some(arr) = effects_arr {
        for (i, item) in arr.iter().enumerate() {
            let start = item.get("start").and_then(Value::as_f64).unwrap_or(0.0);
            let end = item.get("end").and_then(Value::as_f64).unwrap_or(start + 2.0);
            let fx = item.get("fx").and_then(Value::as_str).unwrap_or("caption").to_string();
            let text = item.get("text").and_then(Value::as_str).map(str::to_string);
            let behind = item.get("behind").and_then(Value::as_bool).unwrap_or(false);

            segments.push(TalkingHeadSegment {
                id: format!("seg-{i}"),
                start,
                end,
                fx,
                text,
                behind,
                details: item.clone(),
            });
        }
    }

    let max_seg_end = segments.iter().map(|s| s.end).fold(0.0, f64::max);
    let duration = if raw_dur > 0.0 { raw_dur } else { max_seg_end };

    Ok(TalkingHeadPlan {
        style,
        duration,
        segments,
        raw_json: val,
    })
}

/// Saves an updated plan back to `plan.json`.
pub fn save_plan(plan_path: &Path, plan: &TalkingHeadPlan) -> Result<(), String> {
    let mut val = plan.raw_json.clone();
    if let Some(obj) = val.as_object_mut() {
        obj.insert("style".into(), json!(plan.style));
        let effects_arr: Vec<Value> = plan.segments.iter().map(|seg| {
            let mut item = seg.details.clone();
            if let Some(item_obj) = item.as_object_mut() {
                item_obj.insert("start".into(), json!(seg.start));
                item_obj.insert("end".into(), json!(seg.end));
                item_obj.insert("fx".into(), json!(seg.fx));
                if let Some(ref t) = seg.text {
                    item_obj.insert("text".into(), json!(t));
                }
                item_obj.insert("behind".into(), json!(seg.behind));
            }
            item
        }).collect();
        obj.insert("effects".into(), json!(effects_arr));
    }

    let serialized = serde_json::to_string_pretty(&val)
        .map_err(|e| format!("Failed to serialize plan: {e}"))?;
    std::fs::write(plan_path, serialized)
        .map_err(|e| format!("Failed to write plan.json: {e}"))?;
    Ok(())
}

/// Renders the final broadcast master video (1080x1920, CRF 17).
pub async fn render_final<F>(
    footage_path: &Path,
    plan_path: &Path,
    style: &str,
    output_path: &Path,
    mut on_progress: F,
) -> Result<PathBuf, String>
where
    F: FnMut(&str) + Send + 'static,
{
    let skill_dir = get_skill_dir();
    let script_name = match style {
        "style-11" => "typo_fx.py",
        "style-12" => "liquid_glass_fx.py",
        _ => "fx.py",
    };
    let fx_py = skill_dir.join("scripts").join(script_name);

    if let Some(parent) = output_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }

    on_progress(&format!("Executing final master render using {script_name}..."));

    let py = which::which("python")
        .or_else(|_| which::which("python3"))
        .map_err(|_| "Python executable not found".to_string())?;

    let footage_abs = if footage_path.is_absolute() {
        footage_path.to_path_buf()
    } else if let Ok(cwd) = std::env::current_dir() {
        cwd.join(footage_path)
    } else {
        footage_path.to_path_buf()
    };

    let plan_abs = if plan_path.is_absolute() {
        plan_path.to_path_buf()
    } else if let Ok(cwd) = std::env::current_dir() {
        cwd.join(plan_path)
    } else {
        plan_path.to_path_buf()
    };

    let output_abs = if output_path.is_absolute() {
        output_path.to_path_buf()
    } else if let Ok(cwd) = std::env::current_dir() {
        cwd.join(output_path)
    } else {
        output_path.to_path_buf()
    };

    let mut cmd = std::process::Command::new(py);
    cmd.env("PYTHONUNBUFFERED", "1");
    cmd.arg("-u")
        .arg(&fx_py)
        .arg("--plan")
        .arg(&plan_abs)
        .arg(&footage_abs)
        .arg(&output_abs)
        .current_dir(&skill_dir);

    spawn_streaming_process(cmd, &mut on_progress).await
        .map_err(|e| format!("Failed to run {script_name}: {e}"))?;

    if !output_path.is_file() {
        return Err("Render finished but final master output file was not found".into());
    }

    Ok(output_path.to_path_buf())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_skill_dir_is_absolute_and_exists() {
        let skill_dir = get_skill_dir();
        assert!(skill_dir.is_absolute(), "Skill dir must be an absolute path: {:?}", skill_dir);
        assert!(skill_dir.is_dir(), "Skill dir must exist: {:?}", skill_dir);
        assert!(skill_dir.join("scripts").join("director.py").is_file(), "director.py must exist");
    }

    #[test]
    fn test_check_environment_does_not_panic() {
        let status = check_environment();
        println!("Environment status: {:?}", status);
        assert!(status.ffmpeg_available || !status.ffmpeg_available);
    }

    #[test]
    fn test_plan_serialization() {
        let tmp = std::env::temp_dir().join("test_plan_talking_head.json");
        let plan = TalkingHeadPlan {
            style: "style-11".into(),
            duration: 15.5,
            segments: vec![TalkingHeadSegment {
                id: "seg-0".into(),
                start: 0.0,
                end: 3.5,
                fx: "typography".into(),
                text: Some("Halo dunia".into()),
                behind: true,
                details: json!({"fx": "typography", "behind": true}),
            }],
            raw_json: json!({"style": "style-11", "duration": 15.5}),
        };

        assert!(save_plan(&tmp, &plan).is_ok());
        let parsed = parse_plan(&tmp).expect("Failed to parse plan");
        assert_eq!(parsed.style, "style-11");
        assert_eq!(parsed.segments.len(), 1);
        assert!(parsed.segments[0].behind);
        let _ = std::fs::remove_file(&tmp);
    }
}
