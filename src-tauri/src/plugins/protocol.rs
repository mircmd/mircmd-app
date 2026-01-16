use crate::consts::Dirs;
use std::fs;
use tauri::{
    UriSchemeContext,
    http::{Request, Response, StatusCode, header::CONTENT_TYPE},
};

fn cors_headers(builder: tauri::http::response::Builder) -> tauri::http::response::Builder {
    builder
        .header("Access-Control-Allow-Origin", "*")
        .header("Access-Control-Allow-Methods", "GET, OPTIONS")
        .header("Access-Control-Allow-Headers", "Content-Type, Origin, Accept")
        .header("Access-Control-Max-Age", "86400")
}

pub fn plugin_protocol_handler<R: tauri::Runtime>(
    _ctx: UriSchemeContext<'_, R>,
    request: Request<Vec<u8>>,
) -> Response<Vec<u8>> {
    // Handle CORS preflight
    if request.method() == "OPTIONS" {
        return cors_headers(Response::builder())
            .status(StatusCode::NO_CONTENT)
            .body(Vec::new())
            .unwrap();
    }

    let path = request.uri().path();
    let relative_path = path.trim_start_matches('/');
    let file_path = Dirs::get().plugins.join(relative_path);

    let mime_type = match file_path.extension().and_then(|e| e.to_str()) {
        Some("js") => "text/javascript",
        Some("css") => "text/css",
        Some("html") => "text/html",
        Some("json") => "application/json",
        Some("wasm") => "application/wasm",
        _ => "application/octet-stream",
    };

    if file_path.exists() && file_path.is_file() {
        let content = fs::read(&file_path).unwrap_or_default();

        cors_headers(Response::builder())
            .header(CONTENT_TYPE, mime_type)
            .body(content)
            .unwrap_or_else(|_| {
                Response::builder()
                    .status(StatusCode::INTERNAL_SERVER_ERROR)
                    .body(Vec::new())
                    .unwrap()
            })
    } else {
        cors_headers(Response::builder())
            .status(StatusCode::NOT_FOUND)
            .body("404 Not Found".as_bytes().to_vec())
            .unwrap()
    }
}
