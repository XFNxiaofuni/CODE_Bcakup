import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from tabulate import tabulate

def load_backup_info(backup_dir):
    """加载备份信息"""
    info_file = Path(backup_dir) / 'backup_info.json'
    if not info_file.exists():
        return None
    
    with open(info_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def show_backup_summary(backup_info):
    """显示备份摘要"""
    print("\n=== 备份摘要 ===")
    print(f"备份时间: {backup_info['timestamp']}")
    print(f"描述: {backup_info.get('description', '无')}")
    print(f"标签: {', '.join(backup_info.get('tags', ['无']))}")
    
    # 显示文件统计
    files = backup_info['files']
    total_size = sum(f['size'] for f in files)
    modified_files = sum(1 for f in files if f['changed_since_last_backup'])
    
    print(f"\n总文件数: {len(files)}")
    print(f"总大小: {format_size(total_size)}")
    print(f"修改文件数: {modified_files}")

def show_file_changes(backup_info):
    """显示文件变更"""
    headers = ['文件', '大小', '修改时间', '是否变更']
    rows = []
    
    for file in backup_info['files']:
        rows.append([
            file['path'],
            format_size(file['size']),
            file['modified'],
            '是' if file['changed_since_last_backup'] else '否'
        ])
    
    print("\n=== 文件变更 ===")
    print(tabulate(rows, headers=headers, tablefmt='grid'))

def main():
    parser = argparse.ArgumentParser(description='查看备份信息')
    parser.add_argument('backup_dir', help='备份目录路径')
    parser.add_argument('--files', action='store_true', help='显示文件详情')
    args = parser.parse_args()
    
    backup_info = load_backup_info(args.backup_dir)
    if not backup_info:
        print(f"找不到备份信息文件: {args.backup_dir}/backup_info.json")
        return
    
    show_backup_summary(backup_info)
    if args.files:
        show_file_changes(backup_info)

if __name__ == '__main__':
    main() 