#!/usr/bin/env python3

"""
Cloud Incident Manager
Interactive AWS EKS DevOps Break-Fix Lab

Usage:
    python3 automation/breakfix.py

The lab discovers Kubernetes namespaces and deployments dynamically.
Scenarios require explicit confirmation and preserve recovery backups.
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


BACKUP_DIR = Path(
    os.environ.get(
        "BREAKFIX_BACKUP_DIR",
        Path(__file__).resolve().parent / ".breakfix-backups",
    )
)


SCENARIOS = {
    1: ("Unit Test Failure", "CI/CD"),
    2: ("Dependency Version Conflict", "CI/CD"),
    3: ("Docker Build Failure", "CI/CD"),
    4: ("ECR Authentication Failure", "AWS / CI/CD"),
    5: ("GitHub Actions Permissions", "CI/CD"),
    6: ("Terraform Validation Failure", "Terraform"),
    7: ("Deployment Rollout Failure", "Kubernetes"),
    8: ("Artifact Version Mismatch", "CI/CD"),
    9: ("CrashLoopBackOff", "Kubernetes"),
    10: ("ImagePullBackOff", "Kubernetes"),
    11: ("Persistent Volume Claim Failure", "Kubernetes"),
    12: ("Service Selector Mismatch", "Kubernetes"),
    13: ("OOMKilled", "Kubernetes"),
    14: ("Docker DNS Resolution Failure", "Docker"),
    15: ("Database Authentication Failure", "Database"),
    16: ("Database Migration Failure", "Database"),
    17: ("Redis Queue Failure", "Database / Messaging"),
    18: ("Terraform State Drift", "Terraform / AWS"),
    19: ("Kubernetes NetworkPolicy Failure", "Kubernetes"),
    20: ("Prometheus Monitoring Failure", "Monitoring"),
}


def run_command(command, check=True):
    """Execute a system command and return standard output."""

    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=check,
        )

        return result.stdout.strip()

    except FileNotFoundError:
        raise RuntimeError(
            f"Required command not found: {command[0]}"
        )

    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            exc.stderr.strip()
            or f"Command failed: {' '.join(command)}"
        )


def check_command(name):
    """Check whether an executable is available."""

    try:
        run_command(["which", name])
        return True

    except RuntimeError:
        return False


def confirm(message):
    """Require explicit confirmation."""

    answer = input(
        f"\n{message} (yes/no): "
    ).strip().lower()

    return answer == "yes"


def get_cluster_context():
    """Display the active Kubernetes context."""

    if not check_command("kubectl"):
        raise RuntimeError("kubectl is not installed.")

    context = run_command([
        "kubectl",
        "config",
        "current-context",
    ])

    print(f"\nActive Kubernetes context: {context}")

    return context


def display_menu():
    """Display available break-fix scenarios."""

    print("\n" + "=" * 60)
    print("             CLOUD INCIDENT MANAGER")
    print("                DEVOPS BREAK-FIX LAB")
    print("=" * 60)

    current_category = None

    for number, (name, category) in SCENARIOS.items():

        if category != current_category:
            current_category = category
            print(f"\n--- {category.upper()} ---")

        status = "[READY]" if number == 9 else "[PLANNED]"

        print(f" {number:2}. {name:<38} {status}")

    print("\n  0. Exit")
    print("=" * 60)


def choose_scenario():
    """Prompt the user to select a scenario."""

    while True:

        choice = input(
            "\nChoose a scenario number: "
        ).strip()

        if choice == "0":
            return 0

        try:
            number = int(choice)

        except ValueError:
            print("Please enter a valid number.")
            continue

        if number in SCENARIOS:
            return number

        print("That scenario does not exist.")


def select_deployment():
    """Discover namespaces and let the user select a deployment."""

    output = run_command([
        "kubectl",
        "get",
        "namespaces",
        "-o",
        "json",
    ])

    namespaces = json.loads(output)["items"]

    if not namespaces:
        raise RuntimeError(
            "No Kubernetes namespaces were found."
        )

    print("\nAvailable namespaces:")

    for index, namespace in enumerate(namespaces, 1):

        name = namespace["metadata"]["name"]

        print(f"{index}. {name}")

    while True:

        choice = input(
            "\nSelect namespace: "
        ).strip()

        try:
            index = int(choice) - 1

            if 0 <= index < len(namespaces):

                selected_namespace = (
                    namespaces[index]["metadata"]["name"]
                )

                break

        except ValueError:
            pass

        print("Invalid selection.")

    output = run_command([
        "kubectl",
        "get",
        "deployments",
        "-n",
        selected_namespace,
        "-o",
        "json",
    ])

    deployments = json.loads(output)["items"]

    if not deployments:
        raise RuntimeError(
            f"No deployments found in namespace {selected_namespace}."
        )

    print(
        f"\nAvailable deployments in {selected_namespace}:"
    )

    for index, deployment in enumerate(deployments, 1):

        name = deployment["metadata"]["name"]

        print(f"{index}. {name}")

    while True:

        choice = input(
            "\nSelect deployment: "
        ).strip()

        try:
            index = int(choice) - 1

            if 0 <= index < len(deployments):

                selected = deployments[index]

                return selected_namespace, selected

        except ValueError:
            pass

        print("Invalid selection.")


def inject_crashloop():
    """Inject an invalid container command into a deployment."""

    if not check_command("kubectl"):
        raise RuntimeError("kubectl is not installed.")

    context = get_cluster_context()

    namespace, deployment = select_deployment()

    name = deployment["metadata"]["name"]

    deployment_uid = deployment["metadata"]["uid"]

    containers = (
        deployment["spec"]["template"]["spec"]["containers"]
    )

    if not containers:
        raise RuntimeError(
            "Deployment contains no containers."
        )

    print("\nAvailable containers:")

    for index, container in enumerate(containers, 1):

        print(f"{index}. {container['name']}")

    while True:

        choice = input(
            "\nSelect container: "
        ).strip()

        try:
            index = int(choice) - 1

            if 0 <= index < len(containers):

                container = containers[index]

                break

        except ValueError:
            pass

        print("Invalid selection.")

    container_name = container["name"]

    backup = {
        "scenario": 9,
        "cluster_context": context,
        "namespace": namespace,
        "deployment": name,
        "deployment_uid": deployment_uid,
        "container": container_name,
        "command": container.get("command"),
        "args": container.get("args"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_file = (
        BACKUP_DIR
        / f"K8S-009-{namespace}-{name}-{container_name}.json"
    )

    if backup_file.exists():

        raise RuntimeError(
            "A recovery backup already exists for this target. "
            "Restore the existing scenario before injecting it again."
        )

    print("\nTarget summary")
    print("-" * 45)
    print(f"Cluster:    {context}")
    print(f"Namespace:  {namespace}")
    print(f"Deployment: {name}")
    print(f"Container:  {container_name}")
    print("Failure:    CrashLoopBackOff")
    print("-" * 45)

    if not confirm(
        "This will intentionally break the selected deployment. Continue?"
    ):

        print("Cancelled.")
        return False

    with open(backup_file, "w") as file:

        json.dump(
            backup,
            file,
            indent=2,
        )

    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": container_name,
                            "command": [
                                "/this-command-does-not-exist"
                            ],
                            "args": [],
                        }
                    ]
                }
            }
        }
    }

    try:

        run_command([
            "kubectl",
            "patch",
            "deployment",
            name,
            "-n",
            namespace,
            "--type",
            "strategic",
            "-p",
            json.dumps(patch),
        ])

    except RuntimeError:

        backup_file.unlink(missing_ok=True)

        raise

    print("\n[+] Scenario injected.")
    print(f"[+] Deployment: {name}")
    print(f"[+] Namespace: {namespace}")
    print("[+] Expected symptom: CrashLoopBackOff")
    print(f"[+] Recovery backup: {backup_file}")

    return True


def reset_crashloop():
    """Restore the original container startup configuration."""

    if not BACKUP_DIR.exists():

        print("No recovery backups were found.")

        return

    backups = list(
        BACKUP_DIR.glob("K8S-009-*.json")
    )

    if not backups:

        print("No CrashLoopBackOff backups were found.")

        return

    print("\nAvailable recovery backups:")

    for index, backup in enumerate(backups, 1):

        print(f"{index}. {backup.name}")

    while True:

        choice = input(
            "\nSelect backup to restore: "
        ).strip()

        try:
            index = int(choice) - 1

            if 0 <= index < len(backups):

                backup_file = backups[index]

                break

        except ValueError:
            pass

        print("Invalid selection.")

    with open(backup_file) as file:

        backup = json.load(file)

    context = get_cluster_context()

    if context != backup["cluster_context"]:

        raise RuntimeError(
            "The active Kubernetes context does not match "
            "the cluster where this backup was created."
        )

    current = json.loads(
        run_command([
            "kubectl",
            "get",
            "deployment",
            backup["deployment"],
            "-n",
            backup["namespace"],
            "-o",
            "json",
        ])
    )

    if current["metadata"]["uid"] != backup["deployment_uid"]:

        raise RuntimeError(
            "Deployment identity has changed. "
            "Automatic restoration has been stopped."
        )

    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": backup["container"],
                            "command": backup["command"],
                            "args": backup["args"],
                        }
                    ]
                }
            }
        }
    }

    print("\nRecovery target")
    print("-" * 45)
    print(f"Cluster:    {context}")
    print(f"Namespace:  {backup['namespace']}")
    print(f"Deployment: {backup['deployment']}")
    print(f"Container:  {backup['container']}")
    print("-" * 45)

    if not confirm(
        "Restore the original container configuration?"
    ):

        print("Restoration cancelled.")

        return

    run_command([
        "kubectl",
        "patch",
        "deployment",
        backup["deployment"],
        "-n",
        backup["namespace"],
        "--type",
        "strategic",
        "-p",
        json.dumps(patch),
    ])

    backup_file.unlink()

    print("\n[+] Original container configuration restored.")


def execute_scenario(number):
    """Execute a selected scenario."""

    name, category = SCENARIOS[number]

    print("\n" + "-" * 60)
    print(f"Selected: {name}")
    print(f"Category: {category}")
    print("-" * 60)

    if number != 9:

        print(
            "\n[!] This scenario is registered but not implemented yet."
        )

        print("[!] No resources have been modified.")

        return

    inject_crashloop()


def main():

    print(
        "\nWelcome to the Cloud Incident Manager Break-Fix Lab."
    )

    if not check_command("kubectl"):

        print("\n[!] kubectl is unavailable.")
        print("[!] Kubernetes scenarios will not work.")

    while True:

        display_menu()

        choice = choose_scenario()

        if choice == 0:

            print("\nExiting the Break-Fix Lab.")

            break

        try:

            execute_scenario(choice)

        except (
            RuntimeError,
            json.JSONDecodeError,
            KeyError,
        ) as exc:

            print(f"\n[ERROR] {exc}")

        if choice == 9:

            if confirm(
                "Would you like to restore a previous scenario?"
            ):

                try:

                    reset_crashloop()

                except (
                    RuntimeError,
                    json.JSONDecodeError,
                    KeyError,
                ) as exc:

                    print(
                        f"\n[ERROR] Recovery failed: {exc}"
                    )

        input(
            "\nPress Enter to return to the menu..."
        )


if __name__ == "__main__":
    main()
PY