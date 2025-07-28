import argparse
import json
import os
from typing import List, Dict

DATA_FILE = "tasks.json"


def load_tasks() -> List[Dict]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_tasks(tasks: List[Dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


def add_task(description: str):
    tasks = load_tasks()
    task_id = tasks[-1]["id"] + 1 if tasks else 1
    tasks.append({"id": task_id, "description": description, "done": False})
    save_tasks(tasks)
    print(f"Đã thêm công việc {task_id}: {description}")


def list_tasks():
    tasks = load_tasks()
    if not tasks:
        print("Chưa có công việc nào.")
        return
    for task in tasks:
        status = "x" if task["done"] else " "
        print(f"[{status}] {task['id']}: {task['description']}")


def complete_task(task_id: int):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(tasks)
            print(f"Đã hoàn thành công việc {task_id}")
            return
    print(f"Không tìm thấy công việc {task_id}")


def remove_task(task_id: int):
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        print(f"Không tìm thấy công việc {task_id}")
        return
    save_tasks(new_tasks)
    print(f"Đã xóa công việc {task_id}")


def main():
    parser = argparse.ArgumentParser(description="Quản lý công việc đơn giản")
    subparsers = parser.add_subparsers(dest="command")

    add_p = subparsers.add_parser("add", help="Thêm công việc mới")
    add_p.add_argument("description", nargs="+", help="Nội dung công việc")

    subparsers.add_parser("list", help="Liệt kê công việc")

    done_p = subparsers.add_parser("done", help="Đánh dấu hoàn thành")
    done_p.add_argument("id", type=int, help="ID công việc")

    rm_p = subparsers.add_parser("remove", help="Xóa công việc")
    rm_p.add_argument("id", type=int, help="ID công việc")

    args = parser.parse_args()
    if args.command == "add":
        add_task(" ".join(args.description))
    elif args.command == "list":
        list_tasks()
    elif args.command == "done":
        complete_task(args.id)
    elif args.command == "remove":
        remove_task(args.id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
