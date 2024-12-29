import argparse
import json
import os
from file_copy import main as file_copy_main

def parse_args():
    parser = argparse.ArgumentParser(description='代码备份工具')
    parser.add_argument('-c', '--config', default='config.json',
                        help='配置文件路径 (默认: config.json)')
    parser.add_argument('-d', '--description',
                        help='备份描述 (覆盖配置文件中的描述)')
    parser.add_argument('--tags', nargs='+',
                        help='备份标签 (覆盖配置文件中的标签)')
    parser.add_argument('--no-compress', action='store_true',
                        help='不压缩备份文件')
    return parser.parse_args()

def run_backup(backup_args):
    """执行备份操作"""
    # 读取配置文件
    with open(backup_args['config'], 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 使用命令行参数覆盖配置
    if backup_args['description']:
        config['description'] = backup_args['description']
    if backup_args['tags']:
        config['tags'] = backup_args['tags']
    if backup_args['no_compress']:
        config['compress_backup'] = False
    
    # 运行备份，传递配置参数
    file_copy_main(config)

def main():
    """当作为独立脚本运行时的入口点"""
    args = parse_args()
    backup_args = {
        'config': args.config,
        'description': args.description,
        'tags': args.tags,
        'no_compress': args.no_compress
    }
    run_backup(backup_args)

if __name__ == '__main__':
    main() 