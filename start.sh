#!/bin/bash

# 定义虚拟环境名称、Python 解释器路径和 app.py 文件路径
VENV_NAME=".venv"
PYTHON_PATH="python3"
APP_FILE="app.py"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment..."
    "$PYTHON_PATH" -m venv "$VENV_NAME"
fi

# 设置 Python 解释器路径为变量
PYTHON_EXEC="$VENV_NAME/bin/python"

# 安装依赖项
echo "Installing requirements..."
"$PYTHON_EXEC" -m pip install -r requirements.txt -q

# 启动 app.py
echo "Starting the app..."
"$PYTHON_EXEC" "$APP_FILE"