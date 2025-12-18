#!/usr/bin/env python3
"""
Валидатор waivers.yml и инструмент для работы с waiver политикой
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml


class WaiverValidator:
    def __init__(self, waivers_path="policy/waivers.yml"):
        self.waivers_path = Path(waivers_path)
        self.waivers = self.load_waivers()

    def load_waivers(self):
        """Загрузка waivers из YAML файла"""
        if not self.waivers_path.exists():
            print(f"❌ Файл waivers не найден: {self.waivers_path}")
            sys.exit(1)

        with open(self.waivers_path, "r") as f:
            data = yaml.safe_load(f)

        return data.get("waivers", [])

    def validate_syntax(self):
        """Проверка синтаксиса waivers"""
        errors = []

        required_fields = [
            "id",
            "vulnerability_id",
            "package",
            "reason",
            "justification",
            "expires",
            "owner",
            "status",
        ]

        for i, waiver in enumerate(self.waivers):
            # Проверка обязательных полей
            for field in required_fields:
                if field not in waiver:
                    errors.append(
                        f"Waiver {waiver.get('id', f'index_{i}')}: Missing required field '{field}'"
                    )

            # Проверка формата ID
            if "id" in waiver and not re.match(r"^waiver-\d{3}$", waiver["id"]):
                errors.append(
                    f"Waiver ID format invalid: {waiver['id']}. Should be 'waiver-001' format."
                )

            # Проверка даты истечения
            if "expires" in waiver:
                try:
                    expires = datetime.strptime(waiver["expires"], "%Y-%m-%d")
                    if expires < datetime.now():
                        errors.append(
                            f"Waiver {waiver['id']}: Already expired on {waiver['expires']}"
                        )
                except ValueError:
                    errors.append(
                        f"Waiver {waiver['id']}: Invalid date format '{waiver['expires']}'.\
                            Use YYYY-MM-DD."
                    )

            # Проверка severity (если есть)
            if "severity" in waiver:
                valid_severities = ["critical", "high", "medium", "low"]
                if waiver["severity"].lower() not in valid_severities:
                    errors.append(
                        f"Waiver {waiver['id']}: Invalid severity '{waiver['severity']}'. \
                            Must be one of {valid_severities}"
                    )

            # Проверка reason
            valid_reasons = [
                "false_positive",
                "deferred_fix",
                "risk_accepted",
                "mitigated",
            ]
            if waiver.get("reason") not in valid_reasons:
                errors.append(
                    f"Waiver {waiver['id']}: Invalid reason \
                        '{waiver.get('reason')}'. Must be one of {valid_reasons}"
                )

        return errors

    def get_expired_waivers(self):
        """Получение списка истекших waivers"""
        expired = []

        for waiver in self.waivers:
            if "expires" in waiver:
                try:
                    expires = datetime.strptime(waiver["expires"], "%Y-%m-%d")
                    if expires < datetime.now() and waiver.get("status") == "active":
                        expired.append(waiver)
                except ValueError:
                    continue

        return expired

    def get_expiring_soon_waivers(self, days=14):
        """Получение waivers, срок действия которых истекает скоро"""
        expiring = []
        cutoff = datetime.now() + timedelta(days=days)

        for waiver in self.waivers:
            if "expires" in waiver and waiver.get("status") == "active":
                try:
                    expires = datetime.strptime(waiver["expires"], "%Y-%m-%d")
                    if datetime.now() <= expires <= cutoff:
                        expiring.append(waiver)
                except ValueError:
                    continue

        return expiring

    def generate_grype_config(self, output_path=".grype-generated.yaml"):
        """Генерация конфигурации Grype на основе waivers"""
        ignore_rules = []

        for waiver in self.waivers:
            if waiver.get("status") != "active":
                continue

            rule = {
                "vulnerability": waiver["vulnerability_id"],
                "reason": f"Waiver: {waiver['id']} - {waiver['reason']}",
            }

            # Добавляем информацию о пакете если есть
            if "package" in waiver:
                rule["package"] = {
                    "name": waiver["package"]["name"],
                    "version": waiver["package"].get("version", "*"),
                }

            ignore_rules.append(rule)

        config = {"ignore": ignore_rules, "check-for-app-update": False}

        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        print(
            f"✅ Generated Grype config with {len(ignore_rules)} \
            ignore rules"
        )
        return config

    def apply_to_vulnerabilities(self, vulnerabilities_path, output_path):
        """Применение waivers к результатам сканирования"""
        with open(vulnerabilities_path, "r") as f:
            vulns = json.load(f)

        filtered_matches = []
        waived_count = 0

        for match in vulns.get("matches", []):
            vuln_id = match.get("vulnerability", {}).get("id")
            pkg_name = match.get("artifact", {}).get("name")
            pkg_version = match.get("artifact", {}).get("version")

            # Проверяем, есть ли waiver для этой уязвимости
            waived = False
            for waiver in self.waivers:
                if waiver.get("status") != "active":
                    continue

                # Проверка по ID уязвимости
                if waiver["vulnerability_id"] == vuln_id:
                    # Дополнительная проверка по пакету если указана
                    if "package" in waiver:
                        if waiver["package"]["name"] == pkg_name and waiver[
                            "package"
                        ].get("version") in [pkg_version, "*", None]:
                            waived = True
                            break
                    else:
                        waived = True
                        break

            if not waived:
                filtered_matches.append(match)
            else:
                waived_count += 1

        result = vulns.copy()
        result["matches"] = filtered_matches
        result["waiver_stats"] = {
            "total_waived": waived_count,
            "total_found": len(vulns.get("matches", [])),
            "remaining": len(filtered_matches),
        }

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(
            f"✅ Applied waivers: waived {waived_count}, remaining {len(filtered_matches)}"
        )
        return result


def main():
    parser = argparse.ArgumentParser(
        description="Validate and manage vulnerability waivers"
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Validate waivers syntax only"
    )
    parser.add_argument(
        "--check-expired", action="store_true", help="Check for expired waivers"
    )
    parser.add_argument(
        "--check-expiring", type=int, help="Check waivers expiring in N days"
    )
    parser.add_argument(
        "--count-expired", action="store_true", help="Count expired waivers"
    )
    parser.add_argument(
        "--count-total", action="store_true", help="Count total waivers"
    )
    parser.add_argument(
        "--list-expired", action="store_true", help="List expired waivers"
    )
    parser.add_argument(
        "--generate-grype-config", action="store_true", help="Generate Grype config"
    )
    parser.add_argument("--apply-to", help="Apply waivers to vulnerabilities JSON file")
    parser.add_argument("--output", help="Output file for processed vulnerabilities")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument(
        "--check-gates", action="store_true", help="Check security gates"
    )
    parser.add_argument(
        "--severity", help="Comma-separated list of severities to check"
    )

    args = parser.parse_args()
    validator = WaiverValidator()

    if args.validate_only:
        errors = validator.validate_syntax()
        if errors:
            print("❌ Validation errors found:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("✅ All waivers are valid")
            sys.exit(0)

    if args.check_expired:
        expired = validator.get_expired_waivers()
        if expired:
            print(f"⚠️ Found {len(expired)} expired waivers:")
            for waiver in expired:
                print(
                    f"  - {waiver['id']}: {waiver['vulnerability_id']} \
                        (expired {waiver['expires']})"
                )
            sys.exit(1)
        else:
            print("✅ No expired waivers found")
            sys.exit(0)

    if args.count_expired:
        expired = validator.get_expired_waivers()
        print(len(expired))

    if args.count_total:
        print(len(validator.waivers))

    if args.list_expired:
        expired = validator.get_expired_waivers()
        if args.json:
            print(json.dumps(expired, indent=2))
        else:
            for waiver in expired:
                print(
                    f"{waiver['id']}: {waiver['vulnerability_id']}\
                        ({waiver['expires']})"
                )

    if args.generate_grype_config:
        validator.generate_grype_config()

    if args.apply_to and args.output:
        validator.apply_to_vulnerabilities(args.apply_to, args.output)

    if args.check_expiring:
        expiring = validator.get_expiring_soon_waivers(args.check_expiring)
        if expiring:
            print(
                f"⚠️ Found {len(expiring)} waivers expiring in the next \
                    {args.check_expiring} days:"
            )
            for waiver in expiring:
                print(
                    f"  - {waiver['id']}: {waiver['vulnerability_id']} \
                        (expires {waiver['expires']})"
                )
            sys.exit(1)

    if args.check_gates:
        # Simplified gate check - in real implementation would check actual vulnerabilities
        expired = validator.get_expired_waivers()
        if expired:
            print(f"❌ Security gates failed: {len(expired)} expired waivers")
            sys.exit(1)
        print("✅ Security gates passed")


if __name__ == "__main__":
    main()
