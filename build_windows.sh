#!/bin/bash
# 打包脚本 - 创建 Windows 可执行文件
# 使用 PyInstaller 打包 Python 程序

echo "🚀 发票整理工具 - Windows 打包脚本"
echo "===================================="
echo ""

# 检查 pyinstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 安装 PyInstaller..."
    pip3 install pyinstaller -q
fi

echo "✅ PyInstaller 已安装"

# 创建临时打包目录
BUILD_DIR="build_windows"
mkdir -p $BUILD_DIR
cp invoice_organizer.py $BUILD_DIR/

cd $BUILD_DIR

echo ""
echo "🔨 开始打包 Windows 可执行文件..."
echo "（这个过程可能需要几分钟）"
echo ""

# 使用 PyInstaller 打包
# --onefile: 打包成单个文件
# --windowed: GUI 程序（不显示控制台）
# --name: 输出文件名
pyinstaller \
    --onefile \
    --windowed \
    --name "发票整理工具" \
    --add-data "README.md:." \
    --clean \
    --noconfirm \
    invoice_organizer.py 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 打包成功！"
    echo ""
    echo "📁 输出文件:"
    ls -lh dist/
    
    # 复制到上级目录
    cp dist/* ../
    cd ..
    
    echo ""
    echo "🎉 完成！可执行文件已生成:"
    ls -lh *.exe 2>/dev/null || echo "在 $BUILD_DIR/dist/ 目录中"
else
    echo ""
    echo "❌ 打包失败"
    exit 1
fi

# 清理
echo ""
echo "🧹 清理临时文件..."
rm -rf $BUILD_DIR

echo ""
echo "===================================="
echo "打包完成！"
