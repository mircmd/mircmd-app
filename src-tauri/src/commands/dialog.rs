use serde::{Deserialize, Serialize};
use tauri::{WebviewUrl, WebviewWindowBuilder};

#[derive(Debug, Deserialize, Serialize)]
pub enum Window {
    About,
}

struct WindowProps {
    url: String,
    title: String,
    resizable: bool,
    inner_size: (f64, f64),
}

#[tauri::command]
pub async fn open_dialog(app: tauri::AppHandle, window: Window) {
    let props = match window {
        Window::About => WindowProps {
            url: "about.html".to_string(),
            title: "About Mir Commander".to_string(),
            resizable: false,
            inner_size: (500.0, 430.0),
        },
    };
    WebviewWindowBuilder::new(&app, "label", WebviewUrl::App(props.url.into()))
        .title(props.title)
        .resizable(props.resizable)
        .inner_size(props.inner_size.0, props.inner_size.1)
        .build()
        .unwrap();
}
