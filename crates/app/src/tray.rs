//! System tray integration, background running, and window control (Always On Top).
use gpui_kit::Window;
use std::sync::atomic::{AtomicBool, AtomicIsize, Ordering};

static MAIN_HWND: AtomicIsize = AtomicIsize::new(0);
static ALWAYS_ON_TOP: AtomicBool = AtomicBool::new(false);
static RUN_IN_BACKGROUND: AtomicBool = AtomicBool::new(true);

/// Update cached window handle and settings states.
pub fn update_window_state(window: &Window, on_top: bool, in_background: bool) {
    if let Some(hwnd) = get_hwnd(window) {
        MAIN_HWND.store(hwnd, Ordering::SeqCst);
        set_window_icon(hwnd);
    }
    ALWAYS_ON_TOP.store(on_top, Ordering::SeqCst);
    RUN_IN_BACKGROUND.store(in_background, Ordering::SeqCst);
    set_always_on_top(window, on_top);
}

/// Extract native Win32 window HWND if running on Windows.
pub fn get_hwnd(window: &Window) -> Option<isize> {
    #[cfg(target_os = "windows")]
    {
        use raw_window_handle::{HasWindowHandle, RawWindowHandle};
        if let Ok(handle) = HasWindowHandle::window_handle(window) {
            if let RawWindowHandle::Win32(win32) = handle.as_raw() {
                return Some(win32.hwnd.get());
            }
        }
    }
    #[cfg(not(target_os = "windows"))]
    let _ = window;
    None
}

/// Create an HICON from the application PNG icon.
#[cfg(target_os = "windows")]
pub fn create_app_icon(size: i32) -> Option<windows::Win32::UI::WindowsAndMessaging::HICON> {
    use windows::Win32::UI::WindowsAndMessaging::CreateIconFromResourceEx;
    static ICON_PNG: &[u8] = include_bytes!("../icons/icon.png");
    unsafe {
        let icon = CreateIconFromResourceEx(
            ICON_PNG,
            true,
            0x00030000,
            size,
            size,
            Default::default(),
        ).ok()?;
        if icon.is_invalid() {
            None
        } else {
            Some(icon)
        }
    }
}

/// Set window taskbar and title icon.
pub fn set_window_icon(hwnd_raw: isize) {
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::Foundation::{HWND, LPARAM, WPARAM};
        use windows::Win32::UI::WindowsAndMessaging::{
            SendMessageW, ICON_BIG, ICON_SMALL, WM_SETICON,
        };
        if hwnd_raw != 0 {
            let hwnd = HWND(hwnd_raw as _);
            if let Some(hicon_big) = create_app_icon(256) {
                unsafe {
                    let _ = SendMessageW(hwnd, WM_SETICON, WPARAM(ICON_BIG as _), LPARAM(hicon_big.0 as _));
                }
            }
            if let Some(hicon_sm) = create_app_icon(32) {
                unsafe {
                    let _ = SendMessageW(hwnd, WM_SETICON, WPARAM(ICON_SMALL as _), LPARAM(hicon_sm.0 as _));
                }
            }
        }
    }
    #[cfg(not(target_os = "windows"))]
    let _ = hwnd_raw;
}

/// Check if window is maximized (Win32 IsZoomed on Windows).
pub fn is_window_maximized(window: &Window) -> bool {
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::Foundation::HWND;
        use windows::Win32::UI::WindowsAndMessaging::IsZoomed;
        if let Some(hwnd) = get_hwnd(window) {
            unsafe {
                return IsZoomed(HWND(hwnd as _)).as_bool();
            }
        }
    }
    window.is_maximized()
}

/// Toggle maximize / restore.
pub fn toggle_maximize(window: &Window) {
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::Foundation::HWND;
        use windows::Win32::UI::WindowsAndMessaging::{
            IsZoomed, ShowWindow, SW_MAXIMIZE, SW_RESTORE,
        };
        if let Some(hwnd_raw) = get_hwnd(window) {
            unsafe {
                let hwnd = HWND(hwnd_raw as _);
                if IsZoomed(hwnd).as_bool() {
                    let _ = ShowWindow(hwnd, SW_RESTORE);
                } else {
                    let _ = ShowWindow(hwnd, SW_MAXIMIZE);
                }
                return;
            }
        }
    }
    window.zoom_window();
}

#[cfg(test)]
mod tests {
    #[test]
    #[cfg(target_os = "windows")]
    fn test_create_app_icon() {
        let icon_sm = super::create_app_icon(32);
        assert!(icon_sm.is_some(), "create_app_icon(32) returned None!");
        let icon_lg = super::create_app_icon(256);
        assert!(icon_lg.is_some(), "create_app_icon(256) returned None!");
    }
}

/// Set window to be always on top of other windows.
pub fn set_always_on_top(window: &Window, on_top: bool) {
    ALWAYS_ON_TOP.store(on_top, Ordering::SeqCst);
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::Foundation::HWND;
        use windows::Win32::UI::WindowsAndMessaging::{
            SetWindowPos, HWND_NOTOPMOST, HWND_TOPMOST, SWP_NOACTIVATE, SWP_NOMOVE, SWP_NOSIZE,
        };
        if let Some(hwnd_raw) = get_hwnd(window) {
            unsafe {
                let insert_after = if on_top { HWND_TOPMOST } else { HWND_NOTOPMOST };
                let _ = SetWindowPos(
                    HWND(hwnd_raw as _),
                    insert_after,
                    0,
                    0,
                    0,
                    0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
                );
            }
        }
    }
    #[cfg(not(target_os = "windows"))]
    let _ = (window, on_top);
}

/// Hide window to system tray.
pub fn hide_window(window: &Window) {
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::Foundation::HWND;
        use windows::Win32::UI::WindowsAndMessaging::{ShowWindow, SW_HIDE};
        if let Some(hwnd_raw) = get_hwnd(window) {
            unsafe {
                let _ = ShowWindow(HWND(hwnd_raw as _), SW_HIDE);
            }
        }
    }
    #[cfg(not(target_os = "windows"))]
    let _ = window;
}

/// Restore and focus window from system tray.
pub fn restore_window(hwnd_raw: isize) {
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::Foundation::HWND;
        use windows::Win32::UI::WindowsAndMessaging::{
            SetForegroundWindow, ShowWindow, SW_RESTORE, SW_SHOW,
        };
        if hwnd_raw != 0 {
            let hwnd = HWND(hwnd_raw as _);
            unsafe {
                let _ = ShowWindow(hwnd, SW_SHOW);
                let _ = ShowWindow(hwnd, SW_RESTORE);
                let _ = SetForegroundWindow(hwnd);
            }
        }
    }
    #[cfg(not(target_os = "windows"))]
    let _ = hwnd_raw;
}

/// Initialize the system tray icon and background event receiver.
pub fn init_tray() {
    #[cfg(target_os = "windows")]
    {
        static STARTED: std::sync::Once = std::sync::Once::new();
        STARTED.call_once(|| {
            std::thread::spawn(run_tray_loop);
        });
    }
}

#[cfg(target_os = "windows")]
fn run_tray_loop() {
    use windows::core::{w, PCWSTR};
    use windows::Win32::Foundation::{HWND, LPARAM, LRESULT, POINT, WPARAM};
    use windows::Win32::System::LibraryLoader::GetModuleHandleW;
    use windows::Win32::UI::Shell::{
        NOTIFYICONDATAW, Shell_NotifyIconW, NIF_ICON, NIF_MESSAGE, NIF_TIP, NIM_ADD, NIM_DELETE,
    };
    use windows::Win32::UI::WindowsAndMessaging::{
        AppendMenuW, CreatePopupMenu, CreateWindowExW, DefWindowProcW, DestroyMenu,
        DispatchMessageW, GetCursorPos, GetMessageW, LoadIconW, RegisterClassW, SetForegroundWindow,
        TrackPopupMenu, TranslateMessage, IDI_APPLICATION, MF_CHECKED, MF_SEPARATOR,
        MF_STRING, MF_UNCHECKED, MSG, TPM_BOTTOMALIGN, TPM_RIGHTBUTTON, WINDOW_EX_STYLE,
        WM_COMMAND, WM_CONTEXTMENU, WM_DESTROY, WM_LBUTTONDBLCLK, WM_LBUTTONUP, WM_RBUTTONUP,
        WM_USER, WNDCLASSW, WS_POPUP,
    };

    const WM_TRAY_CALLBACK: u32 = WM_USER + 101;
    const IDM_OPEN: usize = 1001;
    const IDM_ALWAYS_ON_TOP: usize = 1002;
    const IDM_QUIT: usize = 1003;

    unsafe extern "system" fn tray_wnd_proc(
        hwnd: HWND,
        msg: u32,
        wparam: WPARAM,
        lparam: LPARAM,
    ) -> LRESULT {
        unsafe {
            match msg {
                WM_TRAY_CALLBACK => {
                    let event = lparam.0 as u32;
                    if event == WM_LBUTTONUP || event == WM_LBUTTONDBLCLK {
                        let main_hwnd = MAIN_HWND.load(Ordering::SeqCst);
                        restore_window(main_hwnd);
                    } else if event == WM_RBUTTONUP || event == WM_CONTEXTMENU {
                        let mut pt = POINT::default();
                        let _ = GetCursorPos(&mut pt);
                        let _ = SetForegroundWindow(hwnd);
                        if let Ok(menu) = CreatePopupMenu() {
                            let _ = AppendMenuW(menu, MF_STRING, IDM_OPEN, w!("Open Clipper Studio"));
                            let on_top = ALWAYS_ON_TOP.load(Ordering::SeqCst);
                            let top_flag = if on_top { MF_CHECKED } else { MF_UNCHECKED };
                            let _ = AppendMenuW(
                                menu,
                                MF_STRING | top_flag,
                                IDM_ALWAYS_ON_TOP,
                                w!("Always on Top"),
                            );
                            let _ = AppendMenuW(menu, MF_SEPARATOR, 0, PCWSTR::null());
                            let _ = AppendMenuW(menu, MF_STRING, IDM_QUIT, w!("Quit Clipper Studio"));

                            let _ = TrackPopupMenu(
                                menu,
                                TPM_RIGHTBUTTON | TPM_BOTTOMALIGN,
                                pt.x,
                                pt.y,
                                0,
                                hwnd,
                                None,
                            );
                            let _ = DestroyMenu(menu);
                        }
                    }
                    LRESULT(0)
                }
                WM_COMMAND => {
                    let id = wparam.0 as usize;
                    if id == IDM_OPEN {
                        let main_hwnd = MAIN_HWND.load(Ordering::SeqCst);
                        restore_window(main_hwnd);
                    } else if id == IDM_ALWAYS_ON_TOP {
                        let next = !ALWAYS_ON_TOP.load(Ordering::SeqCst);
                        ALWAYS_ON_TOP.store(next, Ordering::SeqCst);
                        let main_hwnd = MAIN_HWND.load(Ordering::SeqCst);
                        if main_hwnd != 0 {
                            use windows::Win32::UI::WindowsAndMessaging::{
                                SetWindowPos, HWND_NOTOPMOST, HWND_TOPMOST, SWP_NOACTIVATE,
                                SWP_NOMOVE, SWP_NOSIZE,
                            };
                            let insert = if next { HWND_TOPMOST } else { HWND_NOTOPMOST };
                            let _ = SetWindowPos(
                                HWND(main_hwnd as _),
                                insert,
                                0,
                                0,
                                0,
                                0,
                                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
                            );
                        }
                    } else if id == IDM_QUIT {
                        std::process::exit(0);
                    }
                    LRESULT(0)
                }
                WM_DESTROY => LRESULT(0),
                _ => DefWindowProcW(hwnd, msg, wparam, lparam),
            }
        }
    }

    unsafe {
        let hinstance = GetModuleHandleW(None).unwrap_or_default();
        let class_name = w!("ClipwardTrayWindowClass");
        let wc = WNDCLASSW {
            lpfnWndProc: Some(tray_wnd_proc),
            hInstance: hinstance.into(),
            lpszClassName: class_name,
            ..Default::default()
        };
        let _ = RegisterClassW(&wc);

        let tray_hwnd = match CreateWindowExW(
            WINDOW_EX_STYLE(0),
            class_name,
            w!("ClipwardTray"),
            WS_POPUP,
            0,
            0,
            0,
            0,
            None,
            None,
            hinstance,
            None,
        ) {
            Ok(h) if !h.is_invalid() => h,
            _ => return,
        };

        let icon = create_app_icon(32).unwrap_or_else(|| LoadIconW(None, IDI_APPLICATION).unwrap_or_default());
        let mut nid = NOTIFYICONDATAW {
            cbSize: std::mem::size_of::<NOTIFYICONDATAW>() as u32,
            hWnd: tray_hwnd,
            uID: 1,
            uFlags: NIF_MESSAGE | NIF_ICON | NIF_TIP,
            uCallbackMessage: WM_TRAY_CALLBACK,
            hIcon: icon,
            ..Default::default()
        };
        let tip: Vec<u16> = "Clipper Studio\0".encode_utf16().collect();
        let len = tip.len().min(nid.szTip.len());
        nid.szTip[..len].copy_from_slice(&tip[..len]);

        let _ = Shell_NotifyIconW(NIM_ADD, &nid);

        let mut msg = MSG::default();
        while GetMessageW(&mut msg, None, 0, 0).as_bool() {
            let _ = TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }

        let _ = Shell_NotifyIconW(NIM_DELETE, &nid);
    }
}
