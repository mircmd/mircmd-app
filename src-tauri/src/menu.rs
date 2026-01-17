use crate::app_state::import_files;
use tauri::menu::*;
use tauri::{App, AppHandle, Result, WebviewUrl, WebviewWindowBuilder};

pub fn create_menu(app: &mut App) -> Result<()> {
    let handle = app.handle();
    let menu = Menu::new(handle)?;

    let item_about = MenuItem::with_id(handle, "about", "About Mir Commander", true, None::<&str>)?;
    let item_update = MenuItem::with_id(handle, "check_updates", "Check for Updates...", true, None::<&str>)?;
    let item_import = MenuItem::with_id(handle, "import_files", "Import Files...", true, Some("CmdOrCtrl+I"))?;
    let item_settings = MenuItem::with_id(handle, "settings", "Settings...", true, None::<&str>)?;

    #[cfg(target_os = "macos")]
    {
        let app_submenu = SubmenuBuilder::new(handle, "Mir Commander")
            .item(&item_about)
            .item(&item_update)
            .separator()
            .item(&item_settings)
            .separator()
            .services()
            .separator()
            .quit_with_text("Quit Mir Commander")
            .build()?;

        let file_submenu = SubmenuBuilder::new(handle, "File").item(&item_import).build()?;

        menu.append(&app_submenu)?;
        menu.append(&file_submenu)?;
    }

    #[cfg(not(target_os = "macos"))]
    {
        let file_submenu = SubmenuBuilder::new(handle, "File")
            .item(&item_import)
            .separator()
            .item(&item_settings)
            .separator()
            .quit_with_text("Quit Mir Commander")
            .build()?;

        let help_submenu = SubmenuBuilder::new(handle, "Help")
            .item(&item_about)
            .item(&item_update)
            .build()?;

        menu.append(&file_submenu)?;
        menu.append(&help_submenu)?;
    }

    app.set_menu(menu)?;

    app.on_menu_event(move |app_handle: &AppHandle, event| match event.id().as_ref() {
        "about" => {
            let window_result =
                WebviewWindowBuilder::new(app_handle, "about", WebviewUrl::App("about.html".to_string().into()))
                    .title("About Mir Commander".to_string())
                    .resizable(false)
                    .inner_size(500.0, 430.0)
                    .build();

            match window_result {
                Ok(window) => {
                    #[cfg(not(target_os = "macos"))]
                    {
                        let _ = window.remove_menu();
                    }
                }
                Err(e) => eprintln!("Failed to create about window: {}", e),
            }
        }
        "import_files" => {
            import_files(app_handle.clone(), None);
        }
        "settings" => {
            println!("Click: Settings");
        }
        "check_updates" => {
            println!("Click: Check Updates");
        }
        _ => {
            println!("Other event: {:?}", event.id());
        }
    });

    Ok(())
}
