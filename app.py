"""ModelScope Studio entry point."""

from studio.app import _launch_port, build_app

demo = build_app()


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=_launch_port())
