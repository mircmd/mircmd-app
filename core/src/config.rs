use serde::{Deserialize, Serialize};
use serde_with::{DefaultOnError, serde_as};
use std::fs;
use std::{fs::read_to_string, path::PathBuf};
use tracing::{error, warn};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Language {
    System,
    English,
    Russian,
}

impl Default for Language {
    fn default() -> Self {
        Self::System
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum DockPosition {
    Left,
    Right,
    Bottom,
}

impl Default for DockPosition {
    fn default() -> Self {
        Self::Left
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub struct Dock {
    pub visible: bool,
    pub size: u32,
}

impl Default for Dock {
    fn default() -> Self {
        Self {
            visible: true,
            size: 200,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Panel {
    pub id: String,
    pub dock_position: DockPosition,
    pub visible: bool,
}

impl Default for Panel {
    fn default() -> Self {
        Self {
            id: String::new(),
            dock_position: DockPosition::Left,
            visible: true,
        }
    }
}

fn default_window_pos() -> (i32, i32) {
    (100, 100)
}

fn default_window_size() -> (u32, u32) {
    (1280, 800)
}

fn default_left_dock() -> Dock {
    Dock {
        visible: true,
        size: 200,
    }
}

fn default_right_dock() -> Dock {
    Dock {
        visible: true,
        size: 350,
    }
}

fn default_bottom_dock() -> Dock {
    Dock {
        visible: true,
        size: 150,
    }
}

fn default_panels() -> Vec<Panel> {
    vec![
        Panel {
            id: "builtin:explorer".to_string(),
            dock_position: DockPosition::Left,
            visible: true,
        },
        Panel {
            id: "builtin:console-output".to_string(),
            dock_position: DockPosition::Bottom,
            visible: true,
        },
    ]
}

#[serde_as]
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Window {
    #[serde(default = "default_window_pos")]
    #[serde_as(as = "DefaultOnError")]
    pub pos: (i32, i32),

    #[serde(default = "default_window_size")]
    #[serde_as(as = "DefaultOnError")]
    pub size: (u32, u32),
}

impl Default for Window {
    fn default() -> Self {
        Self {
            pos: default_window_pos(),
            size: default_window_size(),
        }
    }
}

#[serde_as]
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Docks {
    #[serde(default = "default_left_dock")]
    #[serde_as(as = "DefaultOnError")]
    pub left: Dock,

    #[serde(default = "default_right_dock")]
    #[serde_as(as = "DefaultOnError")]
    pub right: Dock,

    #[serde(default = "default_bottom_dock")]
    #[serde_as(as = "DefaultOnError")]
    pub bottom: Dock,
}

impl Default for Docks {
    fn default() -> Self {
        Self {
            left: default_left_dock(),
            right: default_right_dock(),
            bottom: default_bottom_dock(),
        }
    }
}

/// Workspace layout / Control Panel preferences.
#[serde_as]
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Workspace {
    #[serde(default)]
    #[serde_as(as = "DefaultOnError")]
    pub docks: Docks,

    /// Invalid `panels` fails the whole `Workspace` and falls back via `Config`.
    #[serde(default = "default_panels")]
    pub panels: Vec<Panel>,
}

impl Default for Workspace {
    fn default() -> Self {
        Self {
            docks: Docks::default(),
            panels: default_panels(),
        }
    }
}

#[serde_as]
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Config {
    #[serde(skip)]
    path: PathBuf,

    #[serde(skip)]
    bad_file: bool,

    #[serde(default)]
    #[serde_as(as = "DefaultOnError")]
    pub language: Language,

    #[serde(default)]
    #[serde_as(as = "DefaultOnError")]
    pub window: Window,

    #[serde(default)]
    #[serde_as(as = "DefaultOnError")]
    pub workspace: Workspace,
}

impl Config {
    fn new_default(path: PathBuf, bad_file: bool) -> Self {
        Self {
            path,
            bad_file,
            language: Language::System,
            window: Window::default(),
            workspace: Workspace::default(),
        }
    }
    pub fn load(path: PathBuf) -> Self {
        if !path.exists() {
            let cfg = Self::new_default(path.clone(), false);
            cfg.save().ok();
            return cfg;
        }

        let content = read_to_string(path.clone()).unwrap_or_default();
        match serde_yaml::from_str::<Config>(&content) {
            Ok(mut config) => {
                config.path = path;
                config
            }
            Err(e) => {
                error!("Can't load application config file. Invalid YAML format: {}", e);
                Self::new_default(path, true)
            }
        }
    }

    pub fn save(&self) -> Result<(), std::io::Error> {
        if self.bad_file == true {
            warn!("Can't rewrite file with default settings, please fix original file");
            return Ok(());
        }
        let content =
            serde_yaml::to_string(self).map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;
        fs::write(&self.path, content)
    }
}
