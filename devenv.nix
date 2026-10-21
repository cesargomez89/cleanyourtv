{ pkgs, ... }:

{
  # Java 17 for building and testing the Android TV launcher
  languages.java = {
    enable = true;
    jdk.package = pkgs.temurin-bin-17;
  };

  # Android SDK (platform 34, build-tools 34.0.0) so gradle works without Android Studio; sets ANDROID_HOME
  android = {
    enable = true;
    platforms.version = [ "34" ];
    buildTools.version = [ "34.0.0" ];
    emulator.enable = false;
    systemImages.enable = false;
    ndk.enable = false;
  };


  # Python 3.12 with uv for running tooling, safety scripts, and tests
  languages.python = {
    enable = true;
    package = pkgs.python312;
    uv.enable = true;
  };

  # CLI utilities and Android debug bridge tools
  packages = with pkgs; [
    android-tools
    eza
    fd
    jq
    ripgrep
    sd
    uv
  ];

  # uv must use the interpreter picked below and never download its own
  env.UV_PYTHON_DOWNLOADS = "never";

  # Prepare the tools virtualenv and put it first on PATH, so python3 and tools/*.py find adb-shell.
  # macOS 15 blocks LAN sockets for Nix and Homebrew Python (Errno 65), so build the venv with Apple's
  # CommandLineTools Python there. A venv that was built with another interpreter is rebuilt.
  enterShell = ''
    clt_python=/Library/Developer/CommandLineTools/usr/bin/python3
    venv_python=
    if [ "$(uname -s)" = Darwin ] && [ -x "$clt_python" ]; then
      venv_python=$clt_python
    fi
    if [ -d tools/venv ] && [ -n "$venv_python" ] \
        && ! grep -qx "home = $(dirname "$venv_python")" tools/venv/pyvenv.cfg 2>/dev/null; then
      echo "Rebuilding tools/venv with $venv_python..."
      rm -rf tools/venv
    fi
    if [ ! -d tools/venv ]; then
      echo "Creating Python virtualenv in tools/venv..."
      uv venv ''${venv_python:+--python "$venv_python"} tools/venv
    fi
    uv pip install -q -r tools/requirements.txt --python tools/venv/bin/python
    export VIRTUAL_ENV="$PWD/tools/venv"
    export PATH="$VIRTUAL_ENV/bin:$PATH"
  '';

  # Handy shortcuts for common tasks
  scripts = {
    test-tools.exec = "python3 -m unittest discover -s tests -v";
    build-launcher.exec = "cd launcher && ./gradlew assembleRelease";
    test-launcher.exec = "cd launcher && ./gradlew testReleaseUnitTest lintRelease";
    probe-tv.exec = "tools/tv.py --probe";
    verify-closed-port.exec = "tools/adb-closed.py \"$@\"";
  };
}
