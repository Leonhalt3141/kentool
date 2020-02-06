# scripts/
import sys
import pathlib
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(current_dir) + '/../')


if __name__ == "__main__":
    from code_report.report import send_daily_summary

    send_daily_summary()
