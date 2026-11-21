//! Talking Head Director & Reels Motion Graphics Engine.
//!
//! Autonomous AI Director for vertical videos (Instagram Reels, TikTok, YouTube Shorts).
//! Features:
//! - Visual face framing & YuNet 360° tracking
//! - Dead-air audio trimming & auto-reframe 9:16 vertical
//! - Word-level timestamp Whisper speech transcription
//! - Dynamic adaptive style & multi-beat effects mixing
//! - Strict safe zones & behind-head depth masking
//! - Preview-First workflow (keyframe contact sheets & fast 540p proxy)
//! - Interactive Part Editor for fine-tuning
//! - Master broadcast final rendering (1080x1920, CRF 17)
//! - Persistent Global State across tab navigation
//! - Dedicated Talking Head Library & Renders Manager

use crate::models::Settings;
use crate::shell;
use crate::theme::{ActiveTokens, Tokens};
use crate::ui::{self, Btn, Hue, Tone, Truncate, TypeScale, u};
use clipperstudio_core::talking_head::{
    self, EnvironmentStatus, PreviewResults, TalkingHeadExportEntry, TalkingHeadMode,
    TalkingHeadPlan,
};
use gpui_kit::component::input::{Input, InputEvent, InputState};
use gpui_kit::prelude::FluentBuilder as _;
use gpui_kit::*;
use std::path::{Path, PathBuf};

const PROMPT_SUGGESTIONS: [&str; 6] = [
    "Minimalist Editorial Typography",
    "Liquid Glass Spatial 3D",
    "Tech Terminal & Code",
    "Bold Documentary",
    "High-Retention Creator",
    "Fast & Punchy Hustle",
];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TalkingHeadTab {
    Studio,
    Library,
}

pub struct TalkingHeadState {
    pub active_tab: TalkingHeadTab,
    pub input_path: Option<String>,
    pub is_folder: bool,
    pub mode: TalkingHeadMode,
    pub custom_prompt: String,
    pub clean_audio: bool,
    pub env_status: Option<EnvironmentStatus>,
    pub is_processing: bool,
    pub current_step: String,
    pub error_message: Option<String>,
    pub preview_results: Option<PreviewResults>,
    pub final_output: Option<String>,
    // Resilience & Checkpoints
    pub active_work_dir: Option<PathBuf>,
    pub has_cached_words: bool,
    pub has_cached_plan: bool,
    pub recent_logs: Vec<String>,
    pub active_stage: usize,
    pub progress_percent: f64,
    pub library_entries: Vec<TalkingHeadExportEntry>,
}

struct GlobalTalkingHead(Entity<TalkingHeadState>);
impl Global for GlobalTalkingHead {}

impl TalkingHeadState {
    pub fn global(cx: &mut App) -> Entity<TalkingHeadState> {
        if let Some(global) = cx.try_global::<GlobalTalkingHead>() {
            return global.0.clone();
        }
        let env_status = talking_head::check_environment();
        let state = cx.new(|_| TalkingHeadState {
            active_tab: TalkingHeadTab::Studio,
            input_path: None,
            is_folder: false,
            mode: TalkingHeadMode::Automatic,
            custom_prompt: String::new(),
            clean_audio: false,
            env_status: Some(env_status),
            is_processing: false,
            current_step: String::new(),
            error_message: None,
            preview_results: None,
            final_output: None,
            active_work_dir: None,
            has_cached_words: false,
            has_cached_plan: false,
            recent_logs: Vec::new(),
            active_stage: 0,
            progress_percent: 0.0,
            library_entries: Vec::new(),
        });
        cx.set_global(GlobalTalkingHead(state.clone()));
        state
    }
}

pub struct TalkingHeadPage {
    state: Entity<TalkingHeadState>,
    settings: Entity<Settings>,
    scroll: ScrollHandle,
    prompt_input: Entity<InputState>,
    search_input: Entity<InputState>,
    _subscriptions: Vec<Subscription>,
}

impl TalkingHeadPage {
    pub fn new(window: &mut Window, cx: &mut Context<Self>) -> Self {
        let state = TalkingHeadState::global(cx);
        let settings = Settings::global(cx);

        let initial_prompt = state.read(cx).custom_prompt.clone();
        let prompt_input = cx.new(|cx| {
            let mut inp = InputState::new(window, cx)
                .placeholder("e.g. Apple minimalist typography with gold accents, tight pacing, clean voice...");
            if !initial_prompt.is_empty() {
                inp.set_value(initial_prompt, window, cx);
            }
            inp
        });

        let search_input = cx.new(|cx| {
            InputState::new(window, cx).placeholder("Search exported talking head videos...")
        });

        // Load library entries on mount
        let out_dir = settings
            .read(cx)
            .value
            .as_ref()
            .map(|s| s.output_directory.clone())
            .unwrap_or_default();
        let base_path = if out_dir.is_empty() { None } else { Some(Path::new(&out_dir)) };
        let entries = talking_head::load_talking_head_library(base_path);
        state.update(cx, |s, _| {
            s.library_entries = entries;
        });

        let state_for_prompt = state.downgrade();
        let prompt_captured = prompt_input.clone();
        let subscriptions = vec![
            cx.observe(&state, |_, _, cx| cx.notify()),
            cx.subscribe(&prompt_input, move |_, _, event: &InputEvent, cx| {
                if matches!(event, InputEvent::Change) {
                    let val = prompt_captured.read(cx).value().to_string();
                    let _ = state_for_prompt.update(cx, |s, _| {
                        s.custom_prompt = val;
                    });
                }
            }),
            cx.subscribe(&search_input, |_, _, event: &InputEvent, cx| {
                if matches!(event, InputEvent::Change) {
                    cx.notify();
                }
            }),
        ];

        Self {
            state,
            settings,
            scroll: ScrollHandle::new(),
            prompt_input,
            search_input,
            _subscriptions: subscriptions,
        }
    }

    fn on_click(
        &self,
        cx: &Context<Self>,
        f: impl Fn(&mut Self, &mut Window, &mut Context<Self>) + 'static,
    ) -> impl Fn(&ClickEvent, &mut Window, &mut App) + 'static {
        let this = cx.entity().downgrade();
        move |_, window, cx| {
            let _ = this.update(cx, |this, cx| f(this, window, cx));
        }
    }

    fn switch_tab(&mut self, tab: TalkingHeadTab, cx: &mut Context<Self>) {
        self.state.update(cx, |s, cx| {
            s.active_tab = tab;
            cx.notify();
        });
        cx.notify();
    }

    fn reset_for_another(&mut self, window: &mut Window, cx: &mut Context<Self>) {
        self.prompt_input.update(cx, |p, cx| p.set_value("", window, cx));
        self.state.update(cx, |s, cx| {
            s.input_path = None;
            s.is_folder = false;
            s.active_work_dir = None;
            s.has_cached_words = false;
            s.has_cached_plan = false;
            s.preview_results = None;
            s.final_output = None;
            s.error_message = None;
            s.is_processing = false;
            s.progress_percent = 0.0;
            s.recent_logs.clear();
            cx.notify();
        });
        cx.notify();
    }

    fn pick_video_file(&mut self, cx: &mut Context<Self>) {
        let state = self.state.clone();
        cx.spawn(async move |this, cx| {
            let filters = [
                shell::Filter("Video Files", clipperstudio_core::shared::VIDEO_EXTENSIONS),
                shell::Filter("All Files", &["*"]),
            ];
            if let Some(path) = shell::pick_file("Select Talking Head Video", &filters).await {
                let _ = state.update(cx, |s, cx| {
                    s.input_path = Some(path.to_string_lossy().into_owned());
                    s.is_folder = false;
                    s.error_message = None;
                    cx.notify();
                });
                let _ = this.update(cx, |_, cx| cx.notify());
            }
        })
        .detach();
    }

    fn pick_footage_folder(&mut self, cx: &mut Context<Self>) {
        let state = self.state.clone();
        cx.spawn(async move |this, cx| {
            if let Some(path) = shell::pick_folder("Select Raw Footage Folder").await {
                let _ = state.update(cx, |s, cx| {
                    s.input_path = Some(path.to_string_lossy().into_owned());
                    s.is_folder = true;
                    s.error_message = None;
                    cx.notify();
                });
                let _ = this.update(cx, |_, cx| cx.notify());
            }
        })
        .detach();
    }

    fn handle_pipeline_log(s: &mut TalkingHeadState, msg: &str) {
        let msg_trimmed = msg.trim();
        if msg_trimmed.is_empty() {
            return;
        }

        s.current_step = msg_trimmed.to_string();
        if s.recent_logs.len() >= 6 {
            s.recent_logs.remove(0);
        }
        s.recent_logs.push(msg_trimmed.to_string());

        let lower = msg_trimmed.to_lowercase();
        if lower.contains("yunet") || lower.contains("probe") || lower.contains("probing") || lower.contains("geometry") {
            s.active_stage = 0;
            s.progress_percent = s.progress_percent.max(15.0);
        } else if lower.contains("whisper") || lower.contains("transcrib") || lower.contains("words") {
            s.active_stage = 1;
            if let Some(pct) = Self::extract_whisper_percentage(msg_trimmed) {
                s.progress_percent = (25.0 + (pct * 0.4)).clamp(25.0, 65.0);
            } else if lower.contains("cached") || lower.contains("skipping") {
                s.has_cached_words = true;
                s.progress_percent = s.progress_percent.max(65.0);
            } else {
                s.progress_percent = s.progress_percent.max(30.0);
            }
        } else if lower.contains("blueprint") || lower.contains("director") || lower.contains("plan") || lower.contains("analyz") {
            s.active_stage = 2;
            s.progress_percent = s.progress_percent.max(70.0);
        } else if lower.contains("preview") || lower.contains("proxy") || lower.contains("stills") || lower.contains("stage 1/2") || lower.contains("stage 2/2") || lower.contains("rendering effects") {
            s.active_stage = 3;
            if let Some(pct) = Self::extract_render_percentage(msg_trimmed) {
                s.progress_percent = (80.0 + (pct * 0.19)).clamp(80.0, 99.0);
            } else {
                s.progress_percent = s.progress_percent.max(82.0);
            }
        }
    }

    fn extract_whisper_percentage(line: &str) -> Option<f64> {
        if let Some(start) = line.find("Whisper [") {
            let rest = &line[start + 9..];
            if let Some(end) = rest.find("%]") {
                return rest[..end].trim().parse::<f64>().ok();
            }
        }
        None
    }

    fn extract_render_percentage(line: &str) -> Option<f64> {
        if let Some(start) = line.rfind('(') {
            let rest = &line[start + 1..];
            if let Some(end) = rest.find("%)") {
                return rest[..end].trim().parse::<f64>().ok();
            }
        }
        None
    }

    fn start_director(&mut self, cx: &mut Context<Self>) {
        let (input, style, clean_audio, work_dir) = self.state.update(cx, |s, _| {
            let input = s.input_path.clone();
            let prompt = s.custom_prompt.trim().to_string();
            let style = if s.mode == TalkingHeadMode::CustomPrompt && !prompt.is_empty() {
                Some(prompt)
            } else {
                None
            };
            let clean_audio = s.clean_audio;

            s.is_processing = true;
            s.active_stage = 0;
            s.progress_percent = 5.0;
            s.current_step = "Initializing AI Creative Director...".into();
            s.error_message = None;
            s.final_output = None;
            s.recent_logs.clear();
            s.recent_logs.push("Initializing AI Creative Director pipeline...".into());

            let work_dir = if let Some(ref existing) = s.active_work_dir {
                existing.clone()
            } else {
                let created = talking_head::create_temp_work_dir();
                s.active_work_dir = Some(created.clone());
                created
            };

            s.has_cached_words = work_dir.join("words.json").is_file();
            s.has_cached_plan = work_dir.join("plan.json").is_file();

            (input, style, clean_audio, work_dir)
        });

        let Some(input) = input else {
            self.state.update(cx, |s, _| {
                s.is_processing = false;
                s.error_message = Some("Please select a video file or footage folder first.".into());
            });
            cx.notify();
            return;
        };

        let state = self.state.clone();
        cx.spawn(async move |this, cx| {
            let footage_path = PathBuf::from(&input);
            let default_style = style.as_deref().unwrap_or("auto-mix").to_string();

            // 1. Analyze and Plan
            let (tx_plan, mut rx_plan) = tokio::sync::mpsc::unbounded_channel::<String>();
            let plan_fut = talking_head::analyze_and_plan(
                &footage_path,
                &work_dir,
                style.as_deref(),
                clean_audio,
                move |msg| {
                    let _ = tx_plan.send(msg.to_string());
                },
            );
            let mut plan_fut = std::pin::pin!(plan_fut);

            let plan_res = loop {
                tokio::select! {
                    res = &mut plan_fut => break res,
                    Some(msg) = rx_plan.recv() => {
                        let _ = state.update(cx, |s, cx| {
                            Self::handle_pipeline_log(s, &msg);
                            cx.notify();
                        });
                        let _ = this.update(cx, |_, cx| cx.notify());
                    }
                }
            };

            let plan_path = match plan_res {
                Ok(p) => {
                    let _ = state.update(cx, |s, cx| {
                        s.has_cached_plan = true;
                        s.has_cached_words = true;
                        s.active_stage = 3;
                        s.progress_percent = 80.0;
                        cx.notify();
                    });
                    p
                }
                Err(err) => {
                    let _ = state.update(cx, |s, cx| {
                        s.is_processing = false;
                        s.has_cached_words = work_dir.join("words.json").is_file();
                        s.error_message = Some(format!("Analysis failed: {err}"));
                        cx.notify();
                    });
                    let _ = this.update(cx, |_, cx| cx.notify());
                    return;
                }
            };

            // 2. Generate Preview Stills & Proxy
            let (tx_prev, mut rx_prev) = tokio::sync::mpsc::unbounded_channel::<String>();
            let prev_fut = talking_head::generate_preview(
                &footage_path,
                &plan_path,
                &work_dir,
                move |msg| {
                    let _ = tx_prev.send(msg.to_string());
                },
            );
            let mut prev_fut = std::pin::pin!(prev_fut);

            let preview_res = loop {
                tokio::select! {
                    res = &mut prev_fut => break res,
                    Some(msg) = rx_prev.recv() => {
                        let _ = state.update(cx, |s, cx| {
                            Self::handle_pipeline_log(s, &msg);
                            cx.notify();
                        });
                        let _ = this.update(cx, |_, cx| cx.notify());
                    }
                }
            };

            match preview_res {
                Ok((stills, proxy)) => {
                    let parsed_plan = talking_head::parse_plan(&plan_path).unwrap_or(TalkingHeadPlan {
                        style: default_style,
                        duration: 0.0,
                        segments: vec![],
                        raw_json: serde_json::json!({}),
                    });

                    let _ = state.update(cx, |s, cx| {
                        s.is_processing = false;
                        s.progress_percent = 100.0;
                        s.preview_results = Some(PreviewResults {
                            stills_path: stills.to_string_lossy().into_owned(),
                            proxy_video_path: proxy.to_string_lossy().into_owned(),
                            plan_path: plan_path.to_string_lossy().into_owned(),
                            plan: parsed_plan,
                        });
                        cx.notify();
                    });
                }
                Err(err) => {
                    let _ = state.update(cx, |s, cx| {
                        s.is_processing = false;
                        s.has_cached_plan = plan_path.is_file();
                        s.error_message = Some(format!("Preview generation failed: {err}"));
                        cx.notify();
                    });
                }
            }
            let _ = this.update(cx, |_, cx| cx.notify());
        })
        .detach();
    }

    fn resume_preview(&mut self, cx: &mut Context<Self>) {
        let (input, work_dir) = {
            let s = self.state.read(cx);
            (s.input_path.clone(), s.active_work_dir.clone())
        };

        let Some(input) = input else { return; };
        let Some(work_dir) = work_dir else {
            self.start_director(cx);
            return;
        };

        let plan_path = work_dir.join("plan.json");
        if !plan_path.is_file() {
            self.start_director(cx);
            return;
        }

        let footage_path = PathBuf::from(&input);
        self.state.update(cx, |s, cx| {
            s.is_processing = true;
            s.active_stage = 3;
            s.progress_percent = 80.0;
            s.error_message = None;
            s.current_step = "Resuming preview generation from saved edit plan...".into();
            s.recent_logs.clear();
            s.recent_logs.push("Resuming preview generation from checkpoint...".into());
            cx.notify();
        });
        cx.notify();

        let state = self.state.clone();
        cx.spawn(async move |this, cx| {
            let (tx_prev, mut rx_prev) = tokio::sync::mpsc::unbounded_channel::<String>();
            let prev_fut = talking_head::generate_preview(
                &footage_path,
                &plan_path,
                &work_dir,
                move |msg| {
                    let _ = tx_prev.send(msg.to_string());
                },
            );
            let mut prev_fut = std::pin::pin!(prev_fut);

            let preview_res = loop {
                tokio::select! {
                    res = &mut prev_fut => break res,
                    Some(msg) = rx_prev.recv() => {
                        let _ = state.update(cx, |s, cx| {
                            Self::handle_pipeline_log(s, &msg);
                            cx.notify();
                        });
                        let _ = this.update(cx, |_, cx| cx.notify());
                    }
                }
            };

            match preview_res {
                Ok((stills, proxy)) => {
                    let parsed_plan = talking_head::parse_plan(&plan_path).unwrap_or(TalkingHeadPlan {
                        style: "auto-mix".into(),
                        duration: 0.0,
                        segments: vec![],
                        raw_json: serde_json::json!({}),
                    });

                    let _ = state.update(cx, |s, cx| {
                        s.is_processing = false;
                        s.progress_percent = 100.0;
                        s.preview_results = Some(PreviewResults {
                            stills_path: stills.to_string_lossy().into_owned(),
                            proxy_video_path: proxy.to_string_lossy().into_owned(),
                            plan_path: plan_path.to_string_lossy().into_owned(),
                            plan: parsed_plan,
                        });
                        cx.notify();
                    });
                }
                Err(err) => {
                    let _ = state.update(cx, |s, cx| {
                        s.is_processing = false;
                        s.error_message = Some(format!("Preview generation failed: {err}"));
                        cx.notify();
                    });
                }
            }
            let _ = this.update(cx, |_, cx| cx.notify());
        })
        .detach();
    }

    fn restart_from_scratch(&mut self, cx: &mut Context<Self>) {
        self.state.update(cx, |s, cx| {
            if let Some(ref dir) = s.active_work_dir {
                let _ = std::fs::remove_dir_all(dir);
            }
            s.active_work_dir = None;
            s.has_cached_words = false;
            s.has_cached_plan = false;
            s.recent_logs.clear();
            s.error_message = None;
            s.preview_results = None;
            s.final_output = None;
            s.progress_percent = 0.0;
            cx.notify();
        });
        self.start_director(cx);
    }

    fn toggle_behind_head(&mut self, index: usize, cx: &mut Context<Self>) {
        self.state.update(cx, |s, cx| {
            if let Some(ref mut pr) = s.preview_results {
                if let Some(seg) = pr.plan.segments.get_mut(index) {
                    seg.behind = !seg.behind;
                    let _ = talking_head::save_plan(Path::new(&pr.plan_path), &pr.plan);
                    cx.notify();
                }
            }
        });
    }

    fn refresh_preview(&mut self, cx: &mut Context<Self>) {
        let (footage_path, plan_path, work_dir) = {
            let s = self.state.read(cx);
            let Some(ref pr) = s.preview_results else { return; };
            let plan_path = PathBuf::from(&pr.plan_path);
            let footage_path = PathBuf::from(s.input_path.as_deref().unwrap_or(""));
            let work_dir = plan_path.parent().unwrap_or(Path::new(".")).to_path_buf();
            (footage_path, plan_path, work_dir)
        };

        self.state.update(cx, |s, cx| {
            s.is_processing = true;
            s.active_stage = 3;
            s.current_step = "Refreshing preview stills & proxy video...".into();
            cx.notify();
        });
        cx.notify();

        let state = self.state.clone();
        cx.spawn(async move |this, cx| {
            let (tx_prev, mut rx_prev) = tokio::sync::mpsc::unbounded_channel::<String>();
            let prev_fut = talking_head::generate_preview(
                &footage_path,
                &plan_path,
                &work_dir,
                move |msg| {
                    let _ = tx_prev.send(msg.to_string());
                },
            );
            let mut prev_fut = std::pin::pin!(prev_fut);

            let preview_res = loop {
                tokio::select! {
                    res = &mut prev_fut => break res,
                    Some(msg) = rx_prev.recv() => {
                        let _ = state.update(cx, |s, cx| {
                            Self::handle_pipeline_log(s, &msg);
                            cx.notify();
                        });
                        let _ = this.update(cx, |_, cx| cx.notify());
                    }
                }
            };

            let _ = state.update(cx, |s, cx| {
                s.is_processing = false;
                if let Ok((stills, proxy)) = preview_res {
                    if let Some(ref mut cur_pr) = s.preview_results {
                        cur_pr.stills_path = stills.to_string_lossy().into_owned();
                        cur_pr.proxy_video_path = proxy.to_string_lossy().into_owned();
                    }
                }
                cx.notify();
            });
            let _ = this.update(cx, |_, cx| cx.notify());
        })
        .detach();
    }

    fn render_master_final(&mut self, cx: &mut Context<Self>) {
        let (footage_path, plan_path, style, duration, out_file) = {
            let s = self.state.read(cx);
            let Some(ref pr) = s.preview_results else { return; };
            let plan_path = PathBuf::from(&pr.plan_path);
            let footage_path = PathBuf::from(s.input_path.as_deref().unwrap_or(""));
            let style = pr.plan.style.clone();
            let duration = pr.plan.duration;

            let out_dir = self
                .settings
                .read(cx)
                .value
                .as_ref()
                .map(|v| v.output_directory.clone())
                .unwrap_or_default();
            let base_dir = if out_dir.is_empty() { None } else { Some(PathBuf::from(out_dir)) };
            let out_file = talking_head::generate_master_output_path(base_dir.as_deref());
            (footage_path, plan_path, style, duration, out_file)
        };

        self.state.update(cx, |s, cx| {
            s.is_processing = true;
            s.active_stage = 3;
            s.current_step = "Rendering final broadcast master 1080x1920 (CRF 17)...".into();
            s.recent_logs.clear();
            s.recent_logs.push("Starting master 1080x1920 broadcast export...".into());
            cx.notify();
        });
        cx.notify();

        let state = self.state.clone();
        cx.spawn(async move |this, cx| {
            let (tx_render, mut rx_render) = tokio::sync::mpsc::unbounded_channel::<String>();
            let render_fut = talking_head::render_final(
                &footage_path,
                &plan_path,
                &style,
                &out_file,
                move |msg| {
                    let _ = tx_render.send(msg.to_string());
                },
            );
            let mut render_fut = std::pin::pin!(render_fut);

            let res = loop {
                tokio::select! {
                    res = &mut render_fut => break res,
                    Some(msg) = rx_render.recv() => {
                        let _ = state.update(cx, |s, cx| {
                            Self::handle_pipeline_log(s, &msg);
                            cx.notify();
                        });
                        let _ = this.update(cx, |_, cx| cx.notify());
                    }
                }
            };

            let _ = state.update(cx, |s, cx| {
                s.is_processing = false;
                match res {
                    Ok(path) => {
                        let out_str = path.to_string_lossy().into_owned();
                        let title = s.input_path.as_ref()
                            .and_then(|p| Path::new(p).file_name())
                            .map(|n| n.to_string_lossy().into_owned())
                            .unwrap_or_else(|| "Talking Head Reel".into());
                        let file_size = std::fs::metadata(&path).map(|m| m.len()).unwrap_or(0);
                        let timestamp = talking_head::current_timestamp_display();

                        let entry = TalkingHeadExportEntry {
                            file_path: out_str.clone(),
                            title,
                            style: style.clone(),
                            timestamp,
                            duration_seconds: duration,
                            file_size_bytes: file_size,
                        };

                        s.final_output = Some(out_str);
                        s.library_entries.insert(0, entry);
                        talking_head::save_talking_head_library(&s.library_entries);
                    }
                    Err(err) => {
                        s.error_message = Some(format!("Final render failed: {err}"));
                    }
                }
                cx.notify();
            });
            let _ = this.update(cx, |_, cx| cx.notify());
        })
        .detach();
    }

    fn delete_library_entry(&mut self, file_path: &str, cx: &mut Context<Self>) {
        let path = PathBuf::from(file_path);
        if path.is_file() {
            let _ = std::fs::remove_file(&path);
        }
        self.state.update(cx, |s, cx| {
            s.library_entries.retain(|e| e.file_path != file_path);
            talking_head::save_talking_head_library(&s.library_entries);
            cx.notify();
        });
        cx.notify();
    }

    fn open_output_folder(&self, cx: &App) {
        let out_dir = self
            .settings
            .read(cx)
            .value
            .as_ref()
            .map(|s| s.output_directory.clone())
            .unwrap_or_default();
        let base_dir = if out_dir.is_empty() { None } else { Some(Path::new(&out_dir)) };
        let folder = talking_head::get_output_folder(base_dir);
        let path_str = folder.to_string_lossy().into_owned();
        shell::open_direct(&path_str, cx);
    }
}

impl Render for TalkingHeadPage {
    fn render(&mut self, _window: &mut Window, cx: &mut Context<Self>) -> impl IntoElement {
        let t = *cx.tokens();
        let (active_tab, library_count) = {
            let s = self.state.read(cx);
            (s.active_tab, s.library_entries.len())
        };

        div()
            .id("talking-head-page")
            .size_full()
            .overflow_y_scroll()
            .track_scroll(&self.scroll)
            .p(u(24.))
            .child(
                div()
                    .w_full()
                    .max_w(px(960.))
                    .mx_auto()
                    .flex()
                    .flex_col()
                    .gap(u(20.))
                    // 1. Page Header with Status Indicator
                    .child(self.render_header(&t, cx))
                    // 2. Sub-Navigation Tabs (Studio vs Library)
                    .child(self.render_tabs(active_tab, library_count, &t, cx))
                    // 3. Tab Body
                    .child(match active_tab {
                        TalkingHeadTab::Studio => self.render_studio_tab(&t, cx).into_any_element(),
                        TalkingHeadTab::Library => self.render_library_tab(&t, cx).into_any_element(),
                    }),
            )
    }
}

impl TalkingHeadPage {
    fn render_header(&self, t: &Tokens, cx: &App) -> impl IntoElement {
        let (status_text, is_ok) = match &self.state.read(cx).env_status {
            Some(st) => {
                let ok = st.dependencies_installed && st.models_present;
                (if ok { "AI Engine Ready" } else { "Setup Required" }, ok)
            }
            None => ("Probing Environment...", false),
        };

        let badge = div()
            .flex()
            .items_center()
            .gap(u(6.))
            .px(u(10.))
            .py(u(4.))
            .rounded_full()
            .bg(if is_ok { t.tint(0.04) } else { t.tint(0.08) })
            .border_1()
            .border_color(if is_ok { t.stroke } else { t.warning })
            .child(ui::status_dot(if is_ok { Tone::Success } else { Tone::Warning }, false, t))
            .child(
                div()
                    .text_micro()
                    .font_weight(FontWeight::MEDIUM)
                    .text_color(if is_ok { t.ink_secondary } else { t.warning })
                    .child(status_text),
            );

        ui::page_header(
            "Talking Head Director",
            Some("Autonomous AI Creative Director & Motion Graphics Engine for Reels, TikTok & Shorts".into()),
            Some(badge.into_any_element()),
            t,
        )
    }

    fn render_tabs(
        &self,
        active_tab: TalkingHeadTab,
        library_count: usize,
        t: &Tokens,
        cx: &mut Context<Self>,
    ) -> impl IntoElement {
        div()
            .w_full()
            .flex()
            .items_center()
            .justify_between()
            .border_b_1()
            .border_color(t.stroke)
            .pb(u(8.))
            .child(
                div()
                    .flex()
                    .items_center()
                    .gap(u(8.))
                    .child(
                        // Studio & Director Tab
                        div()
                            .id("tab-studio-btn")
                            .cursor_pointer()
                            .flex()
                            .items_center()
                            .gap(u(8.))
                            .px(u(14.))
                            .py(u(6.))
                            .rounded(px(6.))
                            .bg(if active_tab == TalkingHeadTab::Studio { t.tint(0.08) } else { t.tint(0.01) })
                            .border_1()
                            .border_color(if active_tab == TalkingHeadTab::Studio { t.accent } else { t.stroke })
                            .hover(move |st| st.bg(t.tint(0.06)))
                            .child(ui::icon("sparkles").size(u(14.)).text_color(if active_tab == TalkingHeadTab::Studio { t.accent } else { t.ink_secondary }))
                            .child(
                                div()
                                    .text_caption()
                                    .font_weight(if active_tab == TalkingHeadTab::Studio { FontWeight::SEMIBOLD } else { FontWeight::MEDIUM })
                                    .text_color(if active_tab == TalkingHeadTab::Studio { t.ink } else { t.ink_secondary })
                                    .child("Studio & Director"),
                            )
                            .on_click(self.on_click(cx, |this, _, cx| this.switch_tab(TalkingHeadTab::Studio, cx))),
                    )
                    .child(
                        // Library & Renders Tab
                        div()
                            .id("tab-library-btn")
                            .cursor_pointer()
                            .flex()
                            .items_center()
                            .gap(u(8.))
                            .px(u(14.))
                            .py(u(6.))
                            .rounded(px(6.))
                            .bg(if active_tab == TalkingHeadTab::Library { t.tint(0.08) } else { t.tint(0.01) })
                            .border_1()
                            .border_color(if active_tab == TalkingHeadTab::Library { t.accent } else { t.stroke })
                            .hover(move |st| st.bg(t.tint(0.06)))
                            .child(ui::icon("film").size(u(14.)).text_color(if active_tab == TalkingHeadTab::Library { t.accent } else { t.ink_secondary }))
                            .child(
                                div()
                                    .text_caption()
                                    .font_weight(if active_tab == TalkingHeadTab::Library { FontWeight::SEMIBOLD } else { FontWeight::MEDIUM })
                                    .text_color(if active_tab == TalkingHeadTab::Library { t.ink } else { t.ink_secondary })
                                    .child(format!("Library & Renders ({library_count})")),
                            )
                            .on_click(self.on_click(cx, |this, _, cx| this.switch_tab(TalkingHeadTab::Library, cx))),
                    ),
            )
            .child(
                div()
                    .flex()
                    .items_center()
                    .gap(u(6.))
                    .child(
                        Btn::new("open-th-folder-btn")
                            .small()
                            .ghost()
                            .icon("folder")
                            .label("Open Output Folder")
                            .on_click(self.on_click(cx, |this, _, cx| this.open_output_folder(cx))),
                    ),
            )
    }

    fn render_studio_tab(&self, t: &Tokens, cx: &mut Context<Self>) -> impl IntoElement {
        let (is_processing, error_msg, preview_results, final_output) = {
            let s = self.state.read(cx);
            (
                s.is_processing,
                s.error_message.clone(),
                s.preview_results.clone(),
                s.final_output.clone(),
            )
        };

        div()
            .w_full()
            .flex()
            .flex_col()
            .gap(u(20.))
            // 1. Raw Footage Source Card
            .child(self.render_footage_card(t, cx))
            // 2. Creative Direction Card
            .child(self.render_direction_card(t, cx))
            // 3. Progress Card
            .when(is_processing, |c| c.child(self.render_progress_card(t, cx)))
            // 4. Final Export Card (Prominently displayed when render completes)
            .when_some(final_output, |c, out| {
                c.child(self.render_final_card(&out, t, cx))
            })
            // 5. Error Callout
            .when_some(error_msg, |c, err| {
                c.child(self.render_error_callout(&err, t, cx))
            })
            // 6. Preview Gate & Part Editor
            .when_some(preview_results, |c, pr| {
                c.child(self.render_preview_gate(&pr, t, cx))
            })
    }

    fn render_footage_card(&self, t: &Tokens, cx: &mut Context<Self>) -> impl IntoElement {
        let (input_path, is_folder) = {
            let s = self.state.read(cx);
            (s.input_path.clone(), s.is_folder)
        };

        ui::card(t)
            .w_full()
            .overflow_hidden()
            .p(u(18.))
            .flex()
            .flex_col()
            .gap(u(12.))
            .child(
                div()
                    .flex()
                    .items_center()
                    .justify_between()
                    .child(
                        div()
                            .text_body()
                            .font_weight(FontWeight::SEMIBOLD)
                            .text_color(t.ink)
                            .child("1. Raw Footage Source"),
                    )
                    .when_some(input_path.as_ref(), |header, _| {
                        header.child(
                            div()
                                .flex()
                                .gap(u(8.))
                                .child(
                                    Btn::new("change-video")
                                        .small()
                                        .ghost()
                                        .icon("file-video")
                                        .label("Change Video")
                                        .on_click(self.on_click(cx, |this, _, cx| this.pick_video_file(cx))),
                                )
                                .child(
                                    Btn::new("change-folder")
                                        .small()
                                        .ghost()
                                        .icon("folder")
                                        .label("Change Folder")
                                        .on_click(self.on_click(cx, |this, _, cx| this.pick_footage_folder(cx))),
                                ),
                        )
                    }),
            )
            .child(
                if let Some(ref path) = input_path {
                    let file_name = Path::new(path)
                        .file_name()
                        .map(|n| n.to_string_lossy().into_owned())
                        .unwrap_or_else(|| path.clone());

                    div()
                        .w_full()
                        .p(u(14.))
                        .rounded(px(8.))
                        .bg(t.tint(0.04))
                        .border_1()
                        .border_color(t.stroke)
                        .flex()
                        .items_center()
                        .justify_between()
                        .gap(u(12.))
                        .child(
                            div()
                                .flex()
                                .items_center()
                                .gap(u(12.))
                                .min_w_0()
                                .child(ui::icon_tile(if is_folder { "folder" } else { "file-video" }, Hue::Accent, 32., t))
                                .child(
                                    div()
                                        .flex()
                                        .flex_col()
                                        .min_w_0()
                                        .gap(u(2.))
                                        .child(
                                            div()
                                                .min_w_0()
                                                .one_line()
                                                .text_body()
                                                .font_weight(FontWeight::SEMIBOLD)
                                                .text_color(t.ink)
                                                .child(file_name),
                                        )
                                        .child(
                                            div()
                                                .min_w_0()
                                                .one_line()
                                                .text_caption()
                                                .text_color(t.ink_tertiary)
                                                .child(path.clone()),
                                        ),
                                ),
                        )
                        .child(
                            div()
                                .flex_shrink_0()
                                .child(ui::badge(if is_folder { "Multi-Clip Folder" } else { "Single Video" }, Hue::Accent, t)),
                        )
                        .into_any_element()
                } else {
                    div()
                        .w_full()
                        .p(u(24.))
                        .rounded(px(10.))
                        .border_1()
                        .border_dashed()
                        .border_color(t.tint(0.18))
                        .bg(t.tint(0.02))
                        .flex()
                        .flex_col()
                        .items_center()
                        .justify_center()
                        .gap(u(12.))
                        .child(ui::icon_tile("cloud-upload", Hue::Accent, 36., t))
                        .child(
                            div()
                                .flex()
                                .flex_col()
                                .items_center()
                                .gap(u(2.))
                                .child(
                                    div()
                                        .text_body()
                                        .font_weight(FontWeight::SEMIBOLD)
                                        .text_color(t.ink)
                                        .child("Import your talking head footage"),
                                )
                                .child(
                                    div()
                                        .text_caption()
                                        .text_color(t.ink_secondary)
                                        .child("Select a single video or choose a multi-take folder. Supports MP4, MOV, MKV, WebM."),
                                ),
                        )
                        .child(
                            div()
                                .flex()
                                .gap(u(10.))
                                .mt(u(4.))
                                .child(
                                    Btn::new("pick-file-btn")
                                        .primary()
                                        .icon("file-video")
                                        .label("Browse Video File")
                                        .on_click(self.on_click(cx, |this, _, cx| this.pick_video_file(cx))),
                                )
                                .child(
                                    Btn::new("pick-folder-btn")
                                        .ghost()
                                        .icon("folder")
                                        .label("Browse Footage Folder")
                                        .on_click(self.on_click(cx, |this, _, cx| this.pick_footage_folder(cx))),
                                ),
                        )
                        .into_any_element()
                },
            )
    }

    fn render_direction_card(&self, t: &Tokens, cx: &mut Context<Self>) -> impl IntoElement {
        let (mode, clean_audio, has_input, is_processing) = {
            let s = self.state.read(cx);
            (s.mode, s.clean_audio, s.input_path.is_some(), s.is_processing)
        };
        let weak_state = self.state.downgrade();

        ui::card(t)
            .w_full()
            .overflow_hidden()
            .p(u(18.))
            .flex()
            .flex_col()
            .gap(u(16.))
            .child(
                div()
                    .text_body()
                    .font_weight(FontWeight::SEMIBOLD)
                    .text_color(t.ink)
                    .child("2. Creative Direction"),
            )
            // Mode selection tiles (Auto vs Custom)
            .child(
                div()
                    .w_full()
                    .grid()
                    .grid_cols(2)
                    .gap(u(12.))
                    .child(
                        // Autonomous AI Director Card
                        div()
                            .id("mode-auto-tile")
                            .min_w_0()
                            .p(u(14.))
                            .rounded(px(8.))
                            .cursor_pointer()
                            .border_1()
                            .border_color(if mode == TalkingHeadMode::Automatic { t.accent } else { t.stroke })
                            .bg(if mode == TalkingHeadMode::Automatic { t.tint(0.06) } else { t.tint(0.02) })
                            .hover(move |st| st.bg(t.tint(0.04)))
                            .on_click(cx.listener(|this, _, _, cx| {
                                this.state.update(cx, |s, cx| {
                                    s.mode = TalkingHeadMode::Automatic;
                                    cx.notify();
                                });
                                cx.notify();
                            }))
                            .child(
                                div()
                                    .flex()
                                    .items_center()
                                    .justify_between()
                                    .gap(u(8.))
                                    .child(
                                        div()
                                            .flex()
                                            .items_center()
                                            .gap(u(8.))
                                            .min_w_0()
                                            .child(ui::icon("sparkles").size(u(16.)).text_color(t.accent))
                                            .child(
                                                div()
                                                    .font_weight(FontWeight::SEMIBOLD)
                                                    .text_color(t.ink)
                                                    .child("Autonomous AI Director"),
                                            ),
                                    )
                                    .child(
                                        div()
                                            .flex_shrink_0()
                                            .child(ui::badge("Adaptive", Hue::Accent, t)),
                                    ),
                            )
                            .child(
                                div()
                                    .mt(u(6.))
                                    .min_w_0()
                                    .text_caption()
                                    .text_color(t.ink_secondary)
                                    .child("AI Director probes face framing with YuNet, trims dead-air, auto-reframes to 9:16 vertical, and dynamically blends motion typography, b-roll, and depth masking suited to your speech."),
                            ),
                    )
                    .child(
                        // Custom Prompt Card
                        div()
                            .id("mode-custom-tile")
                            .min_w_0()
                            .p(u(14.))
                            .rounded(px(8.))
                            .cursor_pointer()
                            .border_1()
                            .border_color(if mode == TalkingHeadMode::CustomPrompt { t.accent } else { t.stroke })
                            .bg(if mode == TalkingHeadMode::CustomPrompt { t.tint(0.06) } else { t.tint(0.02) })
                            .hover(move |st| st.bg(t.tint(0.04)))
                            .on_click(cx.listener(|this, _, _, cx| {
                                this.state.update(cx, |s, cx| {
                                    s.mode = TalkingHeadMode::CustomPrompt;
                                    cx.notify();
                                });
                                cx.notify();
                            }))
                            .child(
                                div()
                                    .flex()
                                    .items_center()
                                    .justify_between()
                                    .gap(u(8.))
                                    .child(
                                        div()
                                            .flex()
                                            .items_center()
                                            .gap(u(8.))
                                            .min_w_0()
                                            .child(ui::icon("message-square").size(u(16.)).text_color(t.ink_secondary))
                                            .child(
                                                div()
                                                    .font_weight(FontWeight::SEMIBOLD)
                                                    .text_color(t.ink)
                                                    .child("Custom AI Prompt"),
                                            ),
                                    )
                                    .child(
                                        div()
                                            .flex_shrink_0()
                                            .child(ui::badge("Guided Mode", Hue::Neutral, t)),
                                    ),
                            )
                            .child(
                                div()
                                    .mt(u(6.))
                                    .min_w_0()
                                    .text_caption()
                                    .text_color(t.ink_secondary)
                                    .child("Guide the director with aesthetic prompts, target pacing, or brand vibes (e.g. minimal typography, dark mode SaaS, kinetic creator)."),
                            ),
                    ),
            )
            // Custom prompt textarea and suggestions
            .when(mode == TalkingHeadMode::CustomPrompt, |card| {
                let prompt_entity = self.prompt_input.clone();
                let state_ref = self.state.clone();
                card.child(
                    div()
                        .w_full()
                        .flex()
                        .flex_col()
                        .gap(u(8.))
                        .p(u(12.))
                        .rounded(px(8.))
                        .bg(t.tint(0.03))
                        .border_1()
                        .border_color(t.stroke)
                        .child(
                            div()
                                .text_caption()
                                .font_weight(FontWeight::MEDIUM)
                                .text_color(t.ink)
                                .child("Creative Instructions:"),
                        )
                        .child(Input::new(&self.prompt_input))
                        .child(
                            div()
                                .w_full()
                                .flex()
                                .items_start()
                                .gap(u(6.))
                                .child(
                                    div()
                                        .flex_shrink_0()
                                        .text_micro()
                                        .text_color(t.ink_tertiary)
                                        .child("Quick Ideas:"),
                                )
                                .child(
                                    div()
                                        .w_full()
                                        .flex()
                                        .flex_wrap()
                                        .gap(u(6.))
                                        .children(PROMPT_SUGGESTIONS.iter().enumerate().map(|(ix, &sugg)| {
                                            let prompt_ref = prompt_entity.clone();
                                            let state_target = state_ref.clone();
                                            let text = sugg.to_string();
                                            div()
                                                .id(ElementId::from(format!("sugg-{ix}")))
                                                .px(u(8.))
                                                .py(u(2.))
                                                .rounded_full()
                                                .bg(t.tint(0.06))
                                                .border_1()
                                                .border_color(t.stroke)
                                                .cursor_pointer()
                                                .text_micro()
                                                .text_color(t.ink_secondary)
                                                .child(sugg)
                                                .on_click(cx.listener(move |_, _, window, cx| {
                                                    let t_clone = text.clone();
                                                    prompt_ref.update(cx, |input, cx| {
                                                        input.set_value(t_clone.clone(), window, cx);
                                                    });
                                                    state_target.update(cx, |s, _| {
                                                        s.custom_prompt = t_clone;
                                                    });
                                                }))
                                        })),
                                ),
                        ),
                )
            })
            // Clean Audio Toggle
            .child(
                div()
                    .w_full()
                    .flex()
                    .items_center()
                    .justify_between()
                    .gap(u(16.))
                    .p(u(12.))
                    .rounded(px(8.))
                    .bg(t.tint(0.03))
                    .border_1()
                    .border_color(t.stroke)
                    .child(
                        div()
                            .flex()
                            .flex_col()
                            .min_w_0()
                            .child(
                                div()
                                    .text_caption()
                                    .font_weight(FontWeight::MEDIUM)
                                    .text_color(t.ink)
                                    .child("Clean Audio (Zero-SFX Mode)"),
                            )
                            .child(
                                div()
                                    .text_micro()
                                    .text_color(t.ink_secondary)
                                    .child("Preserves the pure spoken voiceover without synthetic whooshes, pops, or transition sounds."),
                            ),
                    )
                    .child(
                        ui::switch(
                            "clean-audio-switch",
                            clean_audio,
                            false,
                            move |on, _, cx| {
                                let _ = weak_state.update(cx, |s, cx| {
                                    s.clean_audio = on;
                                    cx.notify();
                                });
                            },
                            t,
                        ),
                    ),
            )
            // Primary Execute CTA Button
            .child(
                div()
                    .w_full()
                    .mt(u(4.))
                    .child(
                        Btn::new("start-director-cta")
                            .primary()
                            .large()
                            .disabled(!has_input || is_processing)
                            .icon("sparkles")
                            .label("Analyze & Build Preview")
                            .on_click(self.on_click(cx, |this, _, cx| this.start_director(cx))),
                    ),
            )
    }

    fn render_progress_card(&self, t: &Tokens, cx: &App) -> impl IntoElement {
        let (active_stage, progress_percent, current_step, recent_logs) = {
            let s = self.state.read(cx);
            (s.active_stage, s.progress_percent, s.current_step.clone(), s.recent_logs.clone())
        };

        let stages = [
            ("Face & Geometry", "Probing framing & dead-air with YuNet"),
            ("Speech Analysis", "Transcribing words & timestamps with Whisper"),
            ("Adaptive Blueprint", "Synthesizing dynamic styles & safe-zone beats"),
            ("Proxy & Stills", "Encoding 540p fast proxy & keyframe sheets"),
        ];
        let cur_stage = active_stage.min(3);
        let stage_name = stages[cur_stage].0;

        ui::card(t)
            .w_full()
            .overflow_hidden()
            .p(u(18.))
            .bg(t.tint(0.03))
            .border_color(t.accent)
            .flex()
            .flex_col()
            .gap(u(14.))
            // Top header: Title, spinner, percentage badge
            .child(
                div()
                    .flex()
                    .items_center()
                    .justify_between()
                    .gap(u(12.))
                    .child(
                        div()
                            .flex()
                            .items_center()
                            .gap(u(10.))
                            .min_w_0()
                            .child(ui::spinner(20., t.accent))
                            .child(
                                div()
                                    .flex()
                                    .flex_col()
                                    .gap(u(2.))
                                    .min_w_0()
                                    .child(
                                        div()
                                            .text_body()
                                            .font_weight(FontWeight::SEMIBOLD)
                                            .text_color(t.ink)
                                            .child(format!("AI Director Pipeline Active — Step {} of 4: {}", cur_stage + 1, stage_name)),
                                    )
                                    .child(
                                        div()
                                            .text_caption()
                                            .one_line()
                                            .text_color(t.ink_secondary)
                                            .child(current_step),
                                    ),
                            ),
                    )
                    .child(
                        div()
                            .flex_shrink_0()
                            .child(ui::badge(format!("{:.0}%", progress_percent.clamp(0.0, 100.0)), Hue::Accent, t)),
                    ),
            )
            // Progress Bar
            .child(ui::progress_bar(progress_percent, 6.0, t))
            // 4-Stage Visual Stepper Grid
            .child(
                div()
                    .w_full()
                    .grid()
                    .grid_cols(4)
                    .gap(u(8.))
                    .children(stages.iter().enumerate().map(|(ix, (title, desc))| {
                        let is_done = ix < cur_stage;
                        let is_current = ix == cur_stage;

                        let (status_tone, border_c, bg_c) = if is_done {
                            (Tone::Success, t.success.opacity(0.4), t.success.opacity(0.06))
                        } else if is_current {
                            (Tone::Accent, t.accent, t.accent.opacity(0.08))
                        } else {
                            (Tone::Idle, t.stroke, t.tint(0.01))
                        };

                        div()
                            .min_w_0()
                            .p(u(10.))
                            .rounded(px(8.))
                            .border_1()
                            .border_color(border_c)
                            .bg(bg_c)
                            .flex()
                            .flex_col()
                            .gap(u(4.))
                            .child(
                                div()
                                    .flex()
                                    .items_center()
                                    .gap(u(6.))
                                    .child(ui::status_dot(status_tone, is_current, t))
                                    .child(
                                        div()
                                            .one_line()
                                            .text_caption()
                                            .font_weight(if is_current { FontWeight::BOLD } else { FontWeight::MEDIUM })
                                            .text_color(if is_current || is_done { t.ink } else { t.ink_tertiary })
                                            .child(*title),
                                    ),
                            )
                            .child(
                                div()
                                    .text_micro()
                                    .text_color(if is_current { t.ink_secondary } else { t.ink_tertiary })
                                    .child(*desc),
                            )
                    })),
            )
            // Live Console Feed Box
            .child(
                div()
                    .w_full()
                    .rounded(px(8.))
                    .border_1()
                    .border_color(t.stroke)
                    .bg(t.tint(0.02))
                    .p(u(10.))
                    .flex()
                    .flex_col()
                    .gap(u(6.))
                    .child(
                        div()
                            .flex()
                            .items_center()
                            .justify_between()
                            .child(
                                div()
                                    .flex()
                                    .items_center()
                                    .gap(u(6.))
                                    .child(ui::icon("terminal").size(u(12.)).text_color(t.ink_tertiary))
                                    .child(
                                        div()
                                            .text_micro()
                                            .font_weight(FontWeight::MEDIUM)
                                            .text_color(t.ink_tertiary)
                                            .child("Live Engine Activity Feed"),
                                    ),
                            )
                            .child(
                                div()
                                    .text_micro()
                                    .text_color(t.ink_tertiary)
                                    .child("Realtime stream"),
                            ),
                    )
                    .child(
                        div()
                            .flex()
                            .flex_col()
                            .gap(u(3.))
                            .children(
                                if recent_logs.is_empty() {
                                    vec![div()
                                        .text_micro()
                                        .text_color(t.ink_tertiary)
                                        .child("» Starting AI subsystems...")]
                                } else {
                                    recent_logs.iter().map(|line| {
                                        div()
                                            .one_line()
                                            .text_micro()
                                            .text_color(t.ink_secondary)
                                            .child(format!("» {line}"))
                                    }).collect()
                                }
                            ),
                    ),
            )
    }

    fn render_error_callout(&self, err: &str, t: &Tokens, cx: &mut Context<Self>) -> impl IntoElement {
        let (has_plan, has_words) = {
            let s = self.state.read(cx);
            let has_plan = s.has_cached_plan
                || s.active_work_dir.as_ref().map(|d| d.join("plan.json").is_file()).unwrap_or(false);
            let has_words = s.has_cached_words
                || s.active_work_dir.as_ref().map(|d| d.join("words.json").is_file()).unwrap_or(false);
            (has_plan, has_words)
        };

        let recovery_action: Option<AnyElement> = if has_plan {
            Some(
                div()
                    .flex()
                    .items_center()
                    .gap(u(8.))
                    .child(
                        Btn::new("resume-preview-btn")
                            .primary()
                            .small()
                            .icon("refresh-cw")
                            .label("Resume Preview Generation")
                            .on_click(self.on_click(cx, |this, _, cx| this.resume_preview(cx))),
                    )
                    .child(
                        Btn::new("restart-scratch-btn")
                            .ghost()
                            .small()
                            .icon("trash-2")
                            .label("Restart Clean")
                            .on_click(self.on_click(cx, |this, _, cx| this.restart_from_scratch(cx))),
                    )
                    .into_any_element(),
            )
        } else if has_words {
            Some(
                div()
                    .flex()
                    .items_center()
                    .gap(u(8.))
                    .child(
                        Btn::new("retry-plan-btn")
                            .primary()
                            .small()
                            .icon("refresh-cw")
                            .label("Retry Analysis (Whisper Cached)")
                            .on_click(self.on_click(cx, |this, _, cx| this.start_director(cx))),
                    )
                    .child(
                        Btn::new("restart-scratch-btn")
                            .ghost()
                            .small()
                            .icon("trash-2")
                            .label("Restart Clean")
                            .on_click(self.on_click(cx, |this, _, cx| this.restart_from_scratch(cx))),
                    )
                    .into_any_element(),
            )
        } else {
            Some(
                Btn::new("retry-btn")
                    .primary()
                    .small()
                    .icon("refresh-cw")
                    .label("Try Again")
                    .on_click(self.on_click(cx, |this, _, cx| this.start_director(cx)))
                    .into_any_element(),
            )
        };

        let recovery_desc = if has_plan {
            "Speech transcription and Creative Plan are saved in checkpoints. You can resume preview encoding without re-analyzing or re-transcribing."
        } else if has_words {
            "Speech transcription (Whisper) is cached on disk. Retrying will automatically skip transcription and proceed directly to creative planning."
        } else {
            "Check your video file and ensure Python and models are ready."
        };

        ui::callout(
            ui::CalloutTone::Danger,
            Some("Operation Interrupted".into()),
            Some(
                div()
                    .flex()
                    .flex_col()
                    .gap(u(4.))
                    .child(div().child(err.to_string()))
                    .child(
                        div()
                            .text_caption()
                            .font_weight(FontWeight::MEDIUM)
                            .text_color(t.ink)
                            .child(recovery_desc),
                    )
                    .into_any_element(),
            ),
            recovery_action,
            None,
            t,
        )
    }

    fn render_preview_gate(
        &self,
        pr: &PreviewResults,
        t: &Tokens,
        cx: &mut Context<Self>,
    ) -> impl IntoElement {
        let proxy_path_for_click = pr.proxy_video_path.clone();
        let stills_path_for_click = pr.stills_path.clone();
        let proxy_path_for_folder = pr.proxy_video_path.clone();

        ui::card(t)
            .w_full()
            .overflow_hidden()
            .p(u(20.))
            .flex()
            .flex_col()
            .gap(u(16.))
            .child(
                div()
                    .flex()
                    .items_center()
                    .justify_between()
                    .child(
                        div()
                            .flex()
                            .flex_col()
                            .gap(u(2.))
                            .child(
                                div()
                                    .text_title()
                                    .font_weight(FontWeight::BOLD)
                                    .text_color(t.ink)
                                    .child("3. Preview-First Gate"),
                            )
                            .child(
                                div()
                                    .text_caption()
                                    .text_color(t.ink_secondary)
                                    .child(format!(
                                        "Adaptive Style: {} · Duration: {:.1}s · {} Contextual FX",
                                        pr.plan.style,
                                        pr.plan.duration,
                                        pr.plan.segments.len()
                                    )),
                            ),
                    )
                    .child(ui::badge("Preview Ready", Hue::Success, t)),
            )
            // Design Intelligence & Safe Zone Compliance Overview
            .child(
                div()
                    .w_full()
                    .p(u(12.))
                    .rounded(px(8.))
                    .bg(t.tint(0.03))
                    .border_1()
                    .border_color(t.stroke)
                    .flex()
                    .flex_wrap()
                    .items_center()
                    .justify_between()
                    .gap(u(10.))
                    .child(
                        div()
                            .flex()
                            .flex_wrap()
                            .items_center()
                            .gap(u(8.))
                            .child(ui::badge(format!("Design: {}", pr.plan.style), Hue::Accent, t))
                            .child(ui::badge("Universal Social Safe Zone (13.5%–77.2%)", Hue::Success, t))
                            .child(ui::badge("YuNet Face Protection Active", Hue::Neutral, t)),
                    )
                    .child(
                        div()
                            .text_caption()
                            .font_weight(FontWeight::MEDIUM)
                            .text_color(t.ink_secondary)
                            .child(format!("Total: {:.1}s · Safe Framing 9:16", pr.plan.duration)),
                    ),
            )
            // Preview Action Buttons (Reliable direct OS openers)
            .child(
                div()
                    .flex()
                    .items_center()
                    .gap(u(10.))
                    .child(
                        Btn::new("open-proxy-btn")
                            .primary()
                            .icon("play")
                            .label("Play 540p Proxy Video")
                            .on_click(move |_, _, cx| {
                                shell::open_direct(&proxy_path_for_click, cx);
                            }),
                    )
                    .child(
                        Btn::new("open-stills-btn")
                            .ghost()
                            .icon("image")
                            .label("Open Keyframe Contact Sheet")
                            .on_click(move |_, _, cx| {
                                shell::open_direct(&stills_path_for_click, cx);
                            }),
                    )
                    .child(
                        Btn::new("show-proxy-folder-btn")
                            .ghost()
                            .icon("folder")
                            .label("Show in Folder")
                            .on_click(move |_, _, cx| {
                                shell::reveal_direct(&proxy_path_for_folder, cx);
                            }),
                    ),
            )
            // Part Editor (Fine Tuning)
            .child(
                div()
                    .flex()
                    .flex_col()
                    .gap(u(10.))
                    .mt(u(8.))
                    .child(
                        div()
                            .flex()
                            .items_center()
                            .justify_between()
                            .child(
                                div()
                                    .flex()
                                    .flex_col()
                                    .child(
                                        div()
                                            .text_body()
                                            .font_weight(FontWeight::SEMIBOLD)
                                            .text_color(t.ink)
                                            .child("4. Part Editor (Fine-Tune Segments & 3D Depth)"),
                                    )
                                    .child(
                                        div()
                                            .text_caption()
                                            .text_color(t.ink_secondary)
                                            .child("Inspect effects, adjust text, and toggle Behind-Head Depth Masking per beat."),
                                    ),
                            )
                            .child(
                                Btn::new("refresh-preview-btn")
                                    .small()
                                    .ghost()
                                    .icon("refresh-cw")
                                    .label("Refresh Preview")
                                    .on_click(self.on_click(cx, |this, _, cx| this.refresh_preview(cx))),
                            ),
                    )
                    .children(pr.plan.segments.iter().enumerate().map(|(idx, seg)| {
                        let fx_icon = match seg.fx.as_str() {
                            "hook-card" | "headline-box" => "type",
                            "data-compare" | "liquid-glass-graph" | "pop-word" => "trending-up",
                            "slow-push" | "lean-in" | "rack-focus" | "locked-on" => "camera",
                            "captions" => "subtitles",
                            "checklist" => "check-square",
                            _ => "sparkles",
                        };

                        div()
                            .p(u(12.))
                            .rounded(px(8.))
                            .bg(t.tint(0.04))
                            .border_1()
                            .border_color(t.stroke)
                            .flex()
                            .flex_col()
                            .gap(u(8.))
                            .child(
                                div()
                                    .flex()
                                    .items_center()
                                    .justify_between()
                                    .child(
                                        div()
                                            .flex()
                                            .items_center()
                                            .gap(u(8.))
                                            .child(ui::icon(fx_icon).size(u(14.)).text_color(t.accent))
                                            .child(ui::badge(format!("{:.1}s - {:.1}s", seg.start, seg.end), Hue::Neutral, t))
                                            .child(ui::badge(seg.fx.clone(), Hue::Warning, t)),
                                    )
                                    .child(
                                        div()
                                            .id(ElementId::from(format!("behind-head-toggle-{idx}")))
                                            .cursor_pointer()
                                            .px(u(8.))
                                            .py(u(2.))
                                            .rounded_full()
                                            .bg(if seg.behind { t.accent.opacity(0.15) } else { t.tint(0.06) })
                                            .border_1()
                                            .border_color(if seg.behind { t.accent } else { t.stroke })
                                            .text_micro()
                                            .font_weight(if seg.behind { FontWeight::SEMIBOLD } else { FontWeight::NORMAL })
                                            .text_color(if seg.behind { t.accent_fg } else { t.ink_secondary })
                                            .child(if seg.behind { "✓ Behind-Head Depth Mask" } else { "+ Behind-Head Depth" })
                                            .on_click(cx.listener(move |this, _, _, cx| {
                                                this.toggle_behind_head(idx, cx);
                                            })),
                                    ),
                            )
                            .when_some(seg.text.as_ref(), |item, txt| {
                                let display_txt = txt.replace('|', " · ");
                                item.child(
                                    div()
                                        .text_caption()
                                        .text_color(t.ink)
                                        .child(format!("Hook / Phrase: \"{display_txt}\"")),
                                )
                            })
                    })),
            )
            // Final Render Master CTA
            .child(
                div()
                    .mt(u(14.))
                    .pt(u(14.))
                    .border_t_1()
                    .border_color(t.stroke)
                    .flex()
                    .justify_end()
                    .child(
                        Btn::new("render-master-final-btn")
                            .primary()
                            .large()
                            .disabled(self.state.read(cx).is_processing)
                            .icon("video")
                            .label("Render Broadcast Master (1080x1920)")
                            .on_click(self.on_click(cx, |this, _, cx| this.render_master_final(cx))),
                    ),
            )
    }

    fn render_final_card(&self, out: &str, t: &Tokens, cx: &mut Context<Self>) -> impl IntoElement {
        let out_str = out.to_string();
        let out_str2 = out.to_string();
        let file_name = Path::new(out)
            .file_name()
            .map(|n| n.to_string_lossy().into_owned())
            .unwrap_or_else(|| out.to_string());
        let file_size = std::fs::metadata(out).map(|m| m.len()).unwrap_or(0);
        let size_str = Self::format_file_size(file_size);

        ui::card(t)
            .w_full()
            .overflow_hidden()
            .p(u(20.))
            .bg(t.tint(0.06))
            .border_1()
            .border_color(t.accent)
            .flex()
            .flex_col()
            .gap(u(14.))
            .child(
                div()
                    .flex()
                    .items_center()
                    .justify_between()
                    .child(
                        div()
                            .flex()
                            .items_center()
                            .gap(u(10.))
                            .child(ui::icon_tile("circle-check-big", Hue::Success, 36., t))
                            .child(
                                div()
                                    .flex()
                                    .flex_col()
                                    .child(
                                        div()
                                            .text_heading()
                                            .font_weight(FontWeight::BOLD)
                                            .text_color(t.ink)
                                            .child("Broadcast Master Video Ready!"),
                                    )
                                    .child(
                                        div()
                                            .text_caption()
                                            .text_color(t.ink_secondary)
                                            .child("Render finished in broadcast quality. Ready for TikTok, Reels, & Shorts."),
                                    ),
                            ),
                    )
                    .child(
                        div()
                            .flex()
                            .items_center()
                            .gap(u(6.))
                            .child(ui::badge("1080x1920 (9:16)", Hue::Success, t))
                            .child(ui::badge(size_str, Hue::Neutral, t)),
                    ),
            )
            .child(
                div()
                    .p(u(10.))
                    .rounded(px(6.))
                    .bg(t.tint(0.04))
                    .border_1()
                    .border_color(t.stroke)
                    .flex()
                    .flex_col()
                    .gap(u(4.))
                    .child(
                        div()
                            .text_caption()
                            .font_weight(FontWeight::SEMIBOLD)
                            .text_color(t.ink)
                            .child(file_name),
                    )
                    .child(
                        div()
                            .one_line()
                            .text_micro()
                            .text_color(t.ink_secondary)
                            .child(format!("Location: {out}")),
                    ),
            )
            .child(
                div()
                    .flex()
                    .flex_wrap()
                    .items_center()
                    .gap(u(10.))
                    .child(
                        Btn::new("open-final-file-btn")
                            .primary()
                            .icon("play")
                            .label("Play Master Video")
                            .on_click(move |_, _, cx| {
                                shell::open_direct(&out_str, cx);
                            }),
                    )
                    .child(
                        Btn::new("reveal-final-folder-btn")
                            .ghost()
                            .icon("folder")
                            .label("Show in Explorer")
                            .on_click(move |_, _, cx| {
                                shell::reveal_direct(&out_str2, cx);
                            }),
                    )
                    .child(
                        Btn::new("go-library-btn")
                            .ghost()
                            .icon("film")
                            .label("View in Library")
                            .on_click(self.on_click(cx, |this, _, cx| {
                                this.switch_tab(TalkingHeadTab::Library, cx);
                            })),
                    )
                    .child(
                        Btn::new("direct-another-btn")
                            .ghost()
                            .icon("rotate-ccw")
                            .label("Start New Video (Back to Setup)")
                            .on_click(self.on_click(cx, |this, window, cx| {
                                this.reset_for_another(window, cx);
                            })),
                    ),
            )
    }

    fn render_library_tab(&self, t: &Tokens, cx: &mut Context<Self>) -> impl IntoElement {
        let (entries, search_text) = {
            let s = self.state.read(cx);
            (s.library_entries.clone(), self.search_input.read(cx).value().to_lowercase())
        };

        let filtered_entries: Vec<TalkingHeadExportEntry> = entries
            .into_iter()
            .filter(|e| {
                if search_text.is_empty() {
                    true
                } else {
                    e.title.to_lowercase().contains(&search_text)
                        || e.style.to_lowercase().contains(&search_text)
                        || e.file_path.to_lowercase().contains(&search_text)
                }
            })
            .collect();

        div()
            .w_full()
            .flex()
            .flex_col()
            .gap(u(16.))
            // Library Search Bar & Refresh
            .child(
                div()
                    .w_full()
                    .flex()
                    .items_center()
                    .gap(u(10.))
                    .child(
                        div()
                            .flex_1()
                            .child(Input::new(&self.search_input)),
                    )
                    .child(
                        Btn::new("refresh-lib-btn")
                            .ghost()
                            .icon("refresh-cw")
                            .label("Refresh")
                            .on_click(self.on_click(cx, |this, _, cx| {
                                let out_dir = this
                                    .settings
                                    .read(cx)
                                    .value
                                    .as_ref()
                                    .map(|s| s.output_directory.clone())
                                    .unwrap_or_default();
                                let base_path = if out_dir.is_empty() { None } else { Some(Path::new(&out_dir)) };
                                let entries = talking_head::load_talking_head_library(base_path);
                                this.state.update(cx, |s, cx| {
                                    s.library_entries = entries;
                                    cx.notify();
                                });
                            })),
                    ),
            )
            // Empty State
            .when(filtered_entries.is_empty(), |container| {
                container.child(
                    ui::card(t)
                        .w_full()
                        .p(u(32.))
                        .flex()
                        .flex_col()
                        .items_center()
                        .justify_center()
                        .gap(u(12.))
                        .child(ui::icon_tile("film", Hue::Neutral, 40., t))
                        .child(
                            div()
                                .text_heading()
                                .font_weight(FontWeight::BOLD)
                                .text_color(t.ink)
                                .child("No Talking Head Videos Yet"),
                        )
                        .child(
                            div()
                                .text_caption()
                                .text_color(t.ink_secondary)
                                .child("Exported vertical master reels will appear here automatically for playback and file management."),
                        )
                        .child(
                            Btn::new("start-first-reel-btn")
                                .primary()
                                .icon("sparkles")
                                .label("Direct Your First Reel")
                                .on_click(self.on_click(cx, |this, _, cx| {
                                    this.switch_tab(TalkingHeadTab::Studio, cx);
                                })),
                        ),
                )
            })
            // Video Cards List
            .when(!filtered_entries.is_empty(), |container| {
                container.child(
                    div()
                        .w_full()
                        .flex()
                        .flex_col()
                        .gap(u(12.))
                        .children(filtered_entries.into_iter().enumerate().map(|(ix, entry)| {
                            let file_path_play = entry.file_path.clone();
                            let file_path_reveal = entry.file_path.clone();
                            let file_path_delete = entry.file_path.clone();
                            let size_str = Self::format_file_size(entry.file_size_bytes);

                            ui::card(t)
                                .p(u(16.))
                                .flex()
                                .flex_col()
                                .gap(u(12.))
                                .child(
                                    div()
                                        .flex()
                                        .items_center()
                                        .justify_between()
                                        .gap(u(12.))
                                        .child(
                                            div()
                                                .flex()
                                                .items_center()
                                                .gap(u(12.))
                                                .min_w_0()
                                                .child(ui::icon_tile("video", Hue::Accent, 36., t))
                                                .child(
                                                    div()
                                                        .flex()
                                                        .flex_col()
                                                        .min_w_0()
                                                        .gap(u(2.))
                                                        .child(
                                                            div()
                                                                .one_line()
                                                                .text_body()
                                                                .font_weight(FontWeight::SEMIBOLD)
                                                                .text_color(t.ink)
                                                                .child(entry.title),
                                                        )
                                                        .child(
                                                            div()
                                                                .one_line()
                                                                .text_micro()
                                                                .text_color(t.ink_tertiary)
                                                                .child(entry.file_path),
                                                        ),
                                                ),
                                        )
                                        .child(
                                            div()
                                                .flex()
                                                .items_center()
                                                .gap(u(6.))
                                                .child(ui::badge("1080x1920 (9:16)", Hue::Success, t))
                                                .child(ui::badge(size_str, Hue::Neutral, t)),
                                        ),
                                )
                                .child(
                                    div()
                                        .flex()
                                        .items_center()
                                        .justify_between()
                                        .pt(u(8.))
                                        .border_t_1()
                                        .border_color(t.stroke)
                                        .child(
                                            div()
                                                .flex()
                                                .items_center()
                                                .gap(u(6.))
                                                .child(
                                                    div()
                                                        .text_micro()
                                                        .text_color(t.ink_secondary)
                                                        .child(format!("{} · {}", entry.style, entry.timestamp)),
                                                ),
                                        )
                                        .child(
                                            div()
                                                .flex()
                                                .items_center()
                                                .gap(u(8.))
                                                .child(
                                                    Btn::new(ElementId::from(format!("play-lib-{ix}")))
                                                        .primary()
                                                        .small()
                                                        .icon("play")
                                                        .label("Play Video")
                                                        .on_click(move |_, _, cx| {
                                                            shell::open_direct(&file_path_play, cx);
                                                        }),
                                                )
                                                .child(
                                                    Btn::new(ElementId::from(format!("reveal-lib-{ix}")))
                                                        .ghost()
                                                        .small()
                                                        .icon("folder")
                                                        .label("Show in Explorer")
                                                        .on_click(move |_, _, cx| {
                                                            shell::reveal_direct(&file_path_reveal, cx);
                                                        }),
                                                )
                                                .child(
                                                    Btn::new(ElementId::from(format!("del-lib-{ix}")))
                                                        .ghost()
                                                        .small()
                                                        .icon("trash-2")
                                                        .label("Delete")
                                                        .on_click(self.on_click(cx, move |this, _, cx| {
                                                            this.delete_library_entry(&file_path_delete, cx);
                                                        })),
                                                ),
                                        ),
                                )
                        })),
                )
            })
    }

    fn format_file_size(bytes: u64) -> String {
        if bytes >= 1024 * 1024 * 1024 {
            format!("{:.1} GB", bytes as f64 / (1024.0 * 1024.0 * 1024.0))
        } else if bytes >= 1024 * 1024 {
            format!("{:.1} MB", bytes as f64 / (1024.0 * 1024.0))
        } else if bytes >= 1024 {
            format!("{:.1} KB", bytes as f64 / 1024.0)
        } else {
            format!("{bytes} B")
        }
    }
}
