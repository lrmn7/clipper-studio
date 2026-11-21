fn main() {
    #[cfg(target_os = "windows")]
    {
        use std::path::Path;
        use std::process::Command;

        let out_dir = match std::env::var("OUT_DIR") {
            Ok(val) => val,
            Err(_) => return,
        };

        let ico_path = match Path::new("icons/icon.ico").canonicalize() {
            Ok(path) => path,
            Err(_) => return,
        };

        let rc_content = format!("1 ICON \"{}\"\r\n", ico_path.to_str().unwrap_or("").replace('\\', "/"));
        let rc_path = Path::new(&out_dir).join("app.rc");
        let res_path = Path::new(&out_dir).join("app.res");

        if std::fs::write(&rc_path, rc_content).is_err() {
            return;
        }

        let rc_exe = if Command::new("rc.exe").arg("/?").output().is_ok() {
            "rc.exe".to_string()
        } else {
            let possible_paths = [
                r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\rc.exe",
                r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\rc.exe",
                r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22000.0\x64\rc.exe",
                r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\rc.exe",
            ];
            possible_paths
                .iter()
                .find(|p| Path::new(p).exists())
                .copied()
                .unwrap_or("rc.exe")
                .to_string()
        };

        let status = Command::new(&rc_exe)
            .args(["/fo", res_path.to_str().unwrap_or(""), rc_path.to_str().unwrap_or("")])
            .status();

        if let Ok(status) = status {
            if status.success() {
                println!("cargo:rustc-link-arg={}", res_path.display());
            }
        }
        println!("cargo:rerun-if-changed=icons/icon.ico");
    }
}
