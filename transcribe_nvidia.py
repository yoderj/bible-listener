# Sadly, I haven't been able to get this open-source voice-to-text transcription model
# to work yet.  It appears that you need to install it on Linux.
#
# You might also need an NVIDIA graphics card to get this to work.

# Need to get versions specified here before next attempt:
# https://docs.nvidia.com/deeplearning/nemo/user-guide/docs/en/stable/starthere/intro.html
# https://github.com/nvidia/nemo
# https://github.com/NVIDIA/NeMo/issues/1949 -- only linux supported.
# https://github.com/NVIDIA/NeMo/issues/3544 - SOME models do not require a GPU.
# https://github.com/NVIDIA/NeMo/discussions/3553 --
# https://github.com/NVIDIA/NeMo/issues/3449 -- NeMo on Windows requires Windows 10 with insider program + WSL
#  and may require GPUs.
#
# # Consider using this open-source model instead:
# # https://huggingface.co/nvidia/stt_en_conformer_transducer_xlarge


# pip install Cython
# pip install nemo_toolkit[all]
# Had to start this command again a few times because it failed with a timeout (and other errors) at some point.
# Keeps failing...

# https://visualstudio.microsoft.com/visual-cpp-build-tools/
# error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools":
# One download button. It downloads vs_BuildTools.exe. Run it.
# Many options available. Search/select:
# MSVC v140 - VS 2015 C++ build tools (v14.00)
# 3.75 GB required!!!!


# Didn't help:
# ------------
# "C:\Program Files\Python310\python.exe" -m pip install --force-reinstall nemo_toolkit[all]
# ^-- didn't help.
