import os
import subprocess
import sys


def main():
    try:
        # 获取当前脚本所在目录的绝对路径
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # 模块1：处理图片
        print("开始处理图片...")
        # 强制子进程在base_dir目录下运行
        subprocess.run(
            [sys.executable, 'findphoto.py'],
            check=True,
            cwd=base_dir  # 关键修改点：指定工作目录
        )

        # 使用绝对路径检查文件
        path_file = os.path.join(base_dir, 'path.txt')
        if os.path.exists(path_file):
            print("已遍历选定格式图片")
            subprocess.run(
                [sys.executable, 'processimage.py'],
                check=True,
                cwd=base_dir
            )
            print("已分析所筛选图片")
            subprocess.run(
                [sys.executable, 'tag.py'],
                check=True,
                cwd=base_dir
            )
            print("已为所筛选图片注入标签。")
        else:
            print("未找到未标注【已自动标注】的图片。")

        # 模块2：循环处理视频
        print("\n开始处理视频...")
        video_count = 0
        while True:
            # 查找视频（强制指定工作目录）
            subprocess.run(
                [sys.executable, 'findvideo.py'],
                check=True,
                cwd=base_dir
            )

            # 使用绝对路径检查文件
            if not os.path.exists(os.path.join(base_dir, 'path.txt')):
                print("已无未标注【已自动标注】的视频。")
                break

            # 后续处理（保持工作目录一致）
            subprocess.run(
                [sys.executable, 'processvideo.py'],
                check=True,
                cwd=base_dir
            )
            subprocess.run(
                [sys.executable, 'processimage.py'],
                check=True,
                cwd=base_dir
            )
            subprocess.run(
                [sys.executable, 'tag.py'],
                check=True,
                cwd=base_dir
            )

            video_count += 1
            if video_count % 10 == 0:
                print(f"已标注{video_count}个视频")

    except subprocess.CalledProcessError as e:
        print(f"\n错误：在执行 {e.cmd} 时发生错误（返回码：{e.returncode}）")
    except Exception as e:
        print(f"\n未知错误：{str(e)}")
    finally:
        print("\n自动标注结束。")
        input("按任意键继续...")


if __name__ == "__main__":
    main()