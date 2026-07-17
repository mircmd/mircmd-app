use directories::UserDirs;
use std::path::PathBuf;
use std::sync::OnceLock;

pub const BASE_URL: &str = "https://mircmd.com";

#[derive(Debug)]
pub struct Dirs {
    pub config: PathBuf,
    pub logs: PathBuf,
    pub plugins: PathBuf,
}

impl Dirs {
    pub fn get() -> &'static Dirs {
        static DIRS: OnceLock<Dirs> = OnceLock::new();

        DIRS.get_or_init(|| {
            let user_dirs = UserDirs::new().expect("Failed to find home directory");
            let home_dir = user_dirs.home_dir();
            let home_mircmd = home_dir.join(".config").join("mircmd");

            Dirs {
                config: home_mircmd.join("config_new.yaml"),
                logs: home_mircmd.join("logs"),
                plugins: home_mircmd.join("plugins"),
            }
        })
    }
}
