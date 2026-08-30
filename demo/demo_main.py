import json
import os


def load_json(file_path: str) -> dict:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            res = json.load(f)
        if not isinstance(res, dict):
            raise ValueError(
                f"JSON file must contain a dictionary (object): {file_path}"
            )
        return res
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON file: {file_path}")


def verify_password(username: str, password: str) -> bool:
    print("Verifying user credential...")
    print(f"Given Username: {username}")
    print(f'Given Password: {"*" * len(password)}')
    print("Password verified.")
    return True


def submit_reservation(applicant_information: dict, reservation_details: dict, system_settings: dict) -> None:
    print("\n[System Environment Status]")
    print(f"\tSystem ID: {system_settings.get('system_id', 'N/A')}")
    print(f"\tServer Environment: {system_settings.get('server_environment', 'N/A')}")
    print(f"\tMax Reservations/Day: {system_settings.get('max_reservations_per_day', 'N/A')}")

    print("\n[Applicant Information]")
    print(f"\tName: {applicant_information.get('name', 'N/A')}")
    print(f"\tAge: {applicant_information.get('age', 'N/A')}")
    if "gender" in applicant_information:
        print(f"\tGender: {applicant_information['gender']}")
    print(f"\tEmail: {applicant_information.get('email', 'N/A')}")
    print(f"\tPhone: {applicant_information.get('phone', 'N/A')}")

    print("\n[Reservation Details]")
    print(f"\tDate: {reservation_details.get('reservation_date', 'N/A')}")
    print(f"\tStart Time: {reservation_details.get('reservation_time_start', 'N/A')}")
    print(f"\tEnd Time: {reservation_details.get('reservation_time_end', 'N/A')}")
    purposes = reservation_details.get("reservation_purpose", [])
    print(f"\tPurpose: {', '.join(purposes) if isinstance(purposes, list) else purposes}")
    print(f"\tNotes: {reservation_details.get('notes', 'N/A')}")

    print("\nSubmitting reservation...")
    print("Reservation successfully submitted to the booking system.")


def main():
    config_path = "demo/config/main.json"
    main_config = load_json(config_path)

    user_credential = main_config.get("user_credential", {})
    if verify_password(
        username=user_credential.get("username", ""),
        password=user_credential.get("password", ""),
    ):
        applicant_information = main_config.get("applicant_information", {})
        reservation_detail = main_config.get("reservation_detail", {})
        system_settings = main_config.get("system_settings", {})
        submit_reservation(applicant_information, reservation_detail, system_settings)


if __name__ == "__main__":
    main()
