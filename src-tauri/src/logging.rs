use crate::consts::Dirs;
use rolling_file::{BasicRollingFileAppender, RollingConditionBasic};
use time::{UtcOffset, macros::format_description};
use tracing_subscriber::fmt::time::OffsetTime;
use tracing_subscriber::{filter::LevelFilter, prelude::*};

pub fn setup(release: bool) -> anyhow::Result<tracing_appender::non_blocking::WorkerGuard> {
    let log_level = if release { LevelFilter::INFO } else { LevelFilter::INFO };

    let dirs = Dirs::get();
    let log_path = dirs.logs.join("mircmd.log");

    let file_appender =
        BasicRollingFileAppender::new(&log_path, RollingConditionBasic::new().max_size(5 * 1024 * 1024), 3)?;

    let local_offset = UtcOffset::current_local_offset().unwrap_or(UtcOffset::UTC);
    let timer_format = format_description!("[year]-[month]-[day] [hour]:[minute]:[second]");
    let timer = OffsetTime::new(local_offset, timer_format);

    let (non_blocking_file, guard) = tracing_appender::non_blocking(file_appender);

    let console_layer = tracing_subscriber::fmt::layer()
        .with_writer(std::io::stdout)
        .with_timer(timer.clone())
        .with_ansi(true)
        .with_file(false)
        .with_line_number(false)
        .with_filter(log_level);

    let file_layer = tracing_subscriber::fmt::layer()
        .with_timer(timer)
        .with_ansi(false)
        .with_writer(non_blocking_file)
        .with_filter(log_level);

    tracing_subscriber::registry()
        .with(console_layer)
        .with(file_layer)
        .init();

    Ok(guard)
}
