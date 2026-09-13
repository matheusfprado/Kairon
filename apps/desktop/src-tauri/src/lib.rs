use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

use tauri::Manager;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

#[derive(Default)]
struct CoreProcess(Mutex<Option<Child>>);

fn find_project_root(start: &Path) -> Option<PathBuf> {
    start.ancestors().find_map(|directory| {
        let windows_python = directory.join(".venv").join("Scripts").join("python.exe");
        let unix_python = directory.join(".venv").join("bin").join("python");
        (windows_python.exists() || unix_python.exists()).then(|| directory.to_path_buf())
    })
}

fn spawn_core() -> std::io::Result<Child> {
    let current_directory = std::env::current_dir()?;
    let project_root = find_project_root(&current_directory).ok_or_else(|| {
        std::io::Error::new(
            std::io::ErrorKind::NotFound,
            "Kairon project root not found",
        )
    })?;
    let python = if cfg!(target_os = "windows") {
        project_root.join(".venv").join("Scripts").join("python.exe")
    } else {
        project_root.join(".venv").join("bin").join("python")
    };

    let mut command = Command::new(python);
    command
        .args([
            "-m",
            "uvicorn",
            "core.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ])
        .current_dir(project_root)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    #[cfg(target_os = "windows")]
    command.creation_flags(0x08000000);

    command.spawn()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .manage(CoreProcess::default())
        .setup(|app| {
            match spawn_core() {
                Ok(child) => {
                    let process = app.state::<CoreProcess>();
                    *process.0.lock().expect("core process lock poisoned") = Some(child);
                }
                Err(error) => eprintln!("failed to start Kairon core: {error}"),
            }
            Ok(())
        })
        .plugin(tauri_plugin_opener::init())
        .build(tauri::generate_context!())
        .expect("error while building Kairon");

    app.run(|app_handle, event| {
        if let tauri::RunEvent::Exit = event {
            let process = app_handle.state::<CoreProcess>();
            let child = process.0.lock().expect("core process lock poisoned").take();
            if let Some(mut child) = child {
                #[cfg(target_os = "windows")]
                {
                    let _ = Command::new("taskkill")
                        .args(["/PID", &child.id().to_string(), "/T", "/F"])
                        .creation_flags(0x08000000)
                        .stdout(Stdio::null())
                        .stderr(Stdio::null())
                        .status();
                }
                #[cfg(not(target_os = "windows"))]
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    });
}
