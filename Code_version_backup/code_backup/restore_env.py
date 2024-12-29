import os
import argparse
import subprocess
import venv
from pathlib import Path

def create_virtual_env(env_path):
    """创建虚拟环境"""
    venv.create(env_path, with_pip=True)

def install_requirements(env_path, requirements_file):
    """安装依赖包"""
    # 获取虚拟环境的pip路径
    if os.name == 'nt':  # Windows
        pip_path = os.path.join(env_path, 'Scripts', 'pip')
    else:  # Linux/Mac
        pip_path = os.path.join(env_path, 'bin', 'pip')
    
    # 安装依赖
    subprocess.run([pip_path, 'install', '-r', requirements_file], check=True)

def main():
    parser = argparse.ArgumentParser(description='从备份恢复Python环境')
    parser.add_argument('backup_dir', help='备份目录路径')
    parser.add_argument('--env-name', help='要恢复的环境名称')
    args = parser.parse_args()
    
    backup_dir = Path(args.backup_dir)
    
    # 查找requirements文件
    if args.env_name:
        req_file = backup_dir / f'requirements_{args.env_name}.txt'
    else:
        req_files = list(backup_dir.glob('requirements_*.txt'))
        if not req_files:
            req_file = backup_dir / 'requirements.txt'
        else:
            req_file = req_files[0]
    
    if not req_file.exists():
        print(f"找不到requirements文件: {req_file}")
        return
    
    # 创建虚拟环境
    env_name = args.env_name or 'restored_env'
    env_path = Path.home() / '.virtualenvs' / env_name
    print(f"创建虚拟环境: {env_path}")
    create_virtual_env(env_path)
    
    # 安装依赖
    print(f"安装依赖: {req_file}")
    install_requirements(env_path, req_file)
    
    print(f"\n环境恢复完成！")
    print(f"虚拟环境路径: {env_path}")
    if os.name == 'nt':  # Windows
        print(f"激活环境: {env_path}\\Scripts\\activate")
    else:  # Linux/Mac
        print(f"激活环境: source {env_path}/bin/activate")

if __name__ == '__main__':
    main() 