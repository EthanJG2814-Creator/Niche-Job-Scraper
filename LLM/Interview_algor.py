from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"


def load_users() -> dict[str, dict[str, Any]]:
	if not USERS_FILE.exists():
		return {}

	try:
		with USERS_FILE.open("r", encoding="utf-8") as file:
			data = json.load(file)
			return data if isinstance(data, dict) else {}
	except (json.JSONDecodeError, OSError):
		return {}


def save_users(users: dict[str, dict[str, Any]]) -> None:
	with USERS_FILE.open("w", encoding="utf-8") as file:
		json.dump(users, file, indent=2)


def normalized_key(name: str) -> str:
	return name.strip().lower()


def build_full_name(first_name: str, last_name: str) -> str:
	return f"{first_name.strip()} {last_name.strip()}".strip()


def ask_non_empty(prompt: str) -> str:
	while True:
		value = input(prompt).strip()
		if value:
			return value
		print("Please enter a value.")


def ask_optional(prompt: str) -> str:
	return input(prompt).strip()


def collect_work_history_entry() -> dict[str, str]:
	print("\nAdd a work history entry")
	print("Press Enter to skip any question.")
	title = ask_optional("Job title (example: cashier at walmart): ")
	duration = ask_optional("How long did you work there? (years/months): ")

	duties = ask_optional(
		"1) Can you describe the duties and responsibilities of your job?"
	)
	feelings = ask_optional(
		"2) what did you like about your position? what did you least like about your position?"
	)
	technical_skills = ask_optional(
		"3) What technical skills did you learn on the job and how did you use them?"
	)
	people_skills = ask_optional(
		"4) what were the most important decisions on the job? what hav you learned from the job that you have held?"
	)

	return {
		"title": title,
		"duration": duration,
		"duties": duties,
		"feelings": feelings,
		"technical_skills": technical_skills,
		"people_skills": people_skills,
	}


def collect_work_histories() -> list[dict[str, str]]:
	work_histories: list[dict[str, str]] = []
	while True:
		work_histories.append(collect_work_history_entry())
		more = input("Would you like to add another work history? (y/n): ").strip().lower()
		if more != "y":
			break
	return work_histories


def collect_personal_project_entry() -> dict[str, str]:
	print("\nAdd a personal project")
	project_title = ask_non_empty("1) Project title: ")
	duration = ask_non_empty("2) what was the goal of this project?: ")
	goal_and_why = ask_non_empty(
		"3) what motivated you to start this project: "
	)
	technical_skills = ask_non_empty(
		"4) What technical skills did you learn during the project?: "
	)

	return {
		"project_title": project_title,
		"duration": duration,
		"goal_and_why": goal_and_why,
		"technical_skills": technical_skills,
	}


def collect_personal_projects() -> list[dict[str, str]]:
	projects: list[dict[str, str]] = []
	while True:
		projects.append(collect_personal_project_entry())
		more = input("Would you like to add another personal project? (y/n): ").strip().lower()
		if more != "y":
			break
	return projects


def collect_award_entry() -> dict[str, str]:
	print("\nAdd an award or recognition")
	award_title = ask_non_empty("1) What award were you given?: ")
	reason = ask_non_empty("2) Why were you given that award?: ")
	feeling = ask_non_empty("3) How did you feel about that reward?: ")

	return {
		"award_title": award_title,
		"reason": reason,
		"feeling": feeling,
	}


def collect_awards() -> list[dict[str, str]]:
	awards: list[dict[str, str]] = []
	while True:
		awards.append(collect_award_entry())
		more = input("Would you like to add another award? (y/n): ").strip().lower()
		if more != "y":
			break
	return awards


def has_attended_school(profile: dict[str, Any]) -> bool:
	school = str(profile.get("school", "")).strip().lower()
	return school not in {"", "n/a", "na", "none", "did not attend", "no"}


def collect_coursework_entry() -> dict[str, str]:
	print("\nAdd coursework")
	classes_taken = ask_non_empty("1) What classes did you take for your schooling?: ")
	liked_classes = ask_non_empty("2) What classes did you like?: ")
	liked_classes_additional = ask_non_empty("3) What classes did you like?: ")
	notable_projects = ask_non_empty(
		"4) What were some notable projects you completed during your schooling?: "
	)

	return {
		"classes_taken": classes_taken,
		"liked_classes": liked_classes,
		"liked_classes_additional": liked_classes_additional,
		"notable_projects": notable_projects,
	}


def collect_coursework() -> list[dict[str, str]]:
	coursework_entries: list[dict[str, str]] = []
	while True:
		coursework_entries.append(collect_coursework_entry())
		more = input("Would you like to add another coursework entry? (y/n): ").strip().lower()
		if more != "y":
			break
	return coursework_entries


def create_basic_profile() -> dict[str, Any]:
	print("\nCreate your profile")
	first_name = ask_non_empty("First name: ")
	last_name = ask_non_empty("Last name: ")
	major = ask_non_empty("Major: ")
	school = ask_non_empty("University or high school: ")
	name = build_full_name(first_name, last_name)

	return {
		"first_name": first_name,
		"last_name": last_name,
		"name": name,
		"major": major,
		"school": school,
		"work_history": [],
		"personal_projects": [],
		"awards": [],
		"coursework": [],
	}


def select_personal_project_entry(profile: dict[str, Any]) -> int | None:
	projects = profile.get("personal_projects", [])
	if not projects:
		print("No personal project entries available.")
		return None

	print("\nPersonal projects:")
	for i, project in enumerate(projects, start=1):
		print(f"{i}. {project.get('project_title', 'Untitled')} ({project.get('duration', 'N/A')})")

	while True:
		raw = input("Choose project number: ").strip()
		if raw.isdigit():
			selected = int(raw)
			if 1 <= selected <= len(projects):
				return selected - 1
		print("Invalid choice.")


def select_award_entry(profile: dict[str, Any]) -> int | None:
	awards = profile.get("awards", [])
	if not awards:
		print("No award entries available.")
		return None

	print("\nAwards:")
	for i, award in enumerate(awards, start=1):
		print(f"{i}. {award.get('award_title', 'Untitled')}")

	while True:
		raw = input("Choose award number: ").strip()
		if raw.isdigit():
			selected = int(raw)
			if 1 <= selected <= len(awards):
				return selected - 1
		print("Invalid choice.")


def select_coursework_entry(profile: dict[str, Any]) -> int | None:
	coursework = profile.get("coursework", [])
	if not coursework:
		print("No coursework entries available.")
		return None

	print("\nCoursework entries:")
	for i, entry in enumerate(coursework, start=1):
		print(f"{i}. {entry.get('classes_taken', 'Untitled')} ")

	while True:
		raw = input("Choose coursework number: ").strip()
		if raw.isdigit():
			selected = int(raw)
			if 1 <= selected <= len(coursework):
				return selected - 1
		print("Invalid choice.")


def select_work_entry(profile: dict[str, Any]) -> int | None:
	work_history = profile.get("work_history", [])
	if not work_history:
		print("No work history entries available.")
		return None

	print("\nWork history entries:")
	for i, entry in enumerate(work_history, start=1):
		print(f"{i}. {entry.get('title', 'Untitled')} ({entry.get('duration', 'N/A')})")

	while True:
		raw = input("Choose entry number: ").strip()
		if raw.isdigit():
			selected = int(raw)
			if 1 <= selected <= len(work_history):
				return selected - 1
		print("Invalid choice.")


def edit_basic_info(profile: dict[str, Any]) -> None:
	print("\nEdit basic info")
	profile["first_name"] = ask_non_empty(f"First name [{profile.get('first_name', '')}]: ")
	profile["last_name"] = ask_non_empty(f"Last name [{profile.get('last_name', '')}]: ")
	profile["name"] = build_full_name(profile["first_name"], profile["last_name"])
	profile["major"] = ask_non_empty(f"Major [{profile.get('major', '')}]: ")
	profile["school"] = ask_non_empty(f"School [{profile.get('school', '')}]: ")


def edit_work_entry(profile: dict[str, Any]) -> None:
	idx = select_work_entry(profile)
	if idx is None:
		return

	entry = profile["work_history"][idx]
	print("\nLeave blank to keep current value.")

	title = input(f"Title [{entry['title']}]: ").strip()
	duration = input(f"Duration [{entry['duration']}]: ").strip()
	duties = input(f"Duties [{entry['duties']}]: ").strip()
	feelings = input(f"Feelings [{entry['feelings']}]: ").strip()
	technical = input(f"Technical skills [{entry['technical_skills']}]: ").strip()
	people = input(f"People/soft skills [{entry['people_skills']}]: ").strip()

	if title:
		entry["title"] = title
	if duration:
		entry["duration"] = duration
	if duties:
		entry["duties"] = duties
	if feelings:
		entry["feelings"] = feelings
	if technical:
		entry["technical_skills"] = technical
	if people:
		entry["people_skills"] = people


def remove_work_entry(profile: dict[str, Any]) -> None:
	idx = select_work_entry(profile)
	if idx is None:
		return
	removed = profile["work_history"].pop(idx)
	print(f"Removed: {removed.get('title', 'Untitled')}")


def edit_personal_project_entry(profile: dict[str, Any]) -> None:
	idx = select_personal_project_entry(profile)
	if idx is None:
		return

	entry = profile["personal_projects"][idx]
	print("\nLeave blank to keep current value.")

	project_title = input(f"Project title [{entry['project_title']}]: ").strip()
	duration = input(f"Duration [{entry['duration']}]: ").strip()
	goal_and_why = input(f"Goal and why [{entry['goal_and_why']}]: ").strip()
	technical_skills = input(f"Technical skills [{entry['technical_skills']}]: ").strip()

	if project_title:
		entry["project_title"] = project_title
	if duration:
		entry["duration"] = duration
	if goal_and_why:
		entry["goal_and_why"] = goal_and_why
	if technical_skills:
		entry["technical_skills"] = technical_skills


def remove_personal_project_entry(profile: dict[str, Any]) -> None:
	idx = select_personal_project_entry(profile)
	if idx is None:
		return
	removed = profile["personal_projects"].pop(idx)
	print(f"Removed: {removed.get('project_title', 'Untitled')}")


def edit_award_entry(profile: dict[str, Any]) -> None:
	idx = select_award_entry(profile)
	if idx is None:
		return

	entry = profile["awards"][idx]
	print("\nLeave blank to keep current value.")

	award_title = input(f"Award title [{entry['award_title']}]: ").strip()
	reason = input(f"Reason [{entry['reason']}]: ").strip()
	feeling = input(f"Feeling [{entry['feeling']}]: ").strip()

	if award_title:
		entry["award_title"] = award_title
	if reason:
		entry["reason"] = reason
	if feeling:
		entry["feeling"] = feeling


def remove_award_entry(profile: dict[str, Any]) -> None:
	idx = select_award_entry(profile)
	if idx is None:
		return
	removed = profile["awards"].pop(idx)
	print(f"Removed: {removed.get('award_title', 'Untitled')}")


def edit_coursework_entry(profile: dict[str, Any]) -> None:
	idx = select_coursework_entry(profile)
	if idx is None:
		return

	entry = profile["coursework"][idx]
	print("\nLeave blank to keep current value.")

	classes_taken = input(f"Classes taken [{entry['classes_taken']}]: ").strip()
	liked_classes = input(f"Classes liked [{entry['liked_classes']}]: ").strip()
	liked_classes_additional = input(
		f"Classes liked (additional) [{entry['liked_classes_additional']}]: "
	).strip()
	notable_projects = input(f"Notable projects [{entry['notable_projects']}]: ").strip()

	if classes_taken:
		entry["classes_taken"] = classes_taken
	if liked_classes:
		entry["liked_classes"] = liked_classes
	if liked_classes_additional:
		entry["liked_classes_additional"] = liked_classes_additional
	if notable_projects:
		entry["notable_projects"] = notable_projects


def remove_coursework_entry(profile: dict[str, Any]) -> None:
	idx = select_coursework_entry(profile)
	if idx is None:
		return
	removed = profile["coursework"].pop(idx)
	print(f"Removed: {removed.get('classes_taken', 'Untitled')}")


def show_profile(profile: dict[str, Any]) -> None:
	print("\nCurrent profile")
	print(f"First name: {profile.get('first_name', '')}")
	print(f"Last name: {profile.get('last_name', '')}")
	print(f"Name: {profile.get('name', '')}")
	print(f"Major: {profile.get('major', '')}")
	print(f"School: {profile.get('school', '')}")
	print("Work history:")
	work_history = profile.get("work_history", [])
	if not work_history:
		print("- None")
	for i, entry in enumerate(work_history, start=1):
		print(f"- {i}. {entry.get('title', 'Untitled')} ({entry.get('duration', 'N/A')})")
	print("Personal projects:")
	personal_projects = profile.get("personal_projects", [])
	if not personal_projects:
		print("- None")
	for i, entry in enumerate(personal_projects, start=1):
		print(
			f"- {i}. {entry.get('project_title', 'Untitled')} "
			f"({entry.get('duration', 'N/A')})"
		)
	print("Awards:")
	awards = profile.get("awards", [])
	if not awards:
		print("- None")
	for i, entry in enumerate(awards, start=1):
		print(f"- {i}. {entry.get('award_title', 'Untitled')}")
	print("Coursework:")
	coursework = profile.get("coursework", [])
	if not coursework:
		print("- None")
	for i, entry in enumerate(coursework, start=1):
		print(f"- {i}. {entry.get('classes_taken', 'Untitled')}")


def existing_user_menu(users: dict[str, dict[str, Any]], user_key: str) -> None:
	while True:
		profile = users[user_key]
		profile.setdefault("work_history", [])
		profile.setdefault("personal_projects", [])
		profile.setdefault("awards", [])
		profile.setdefault("coursework", [])
		print(
			"\nMenu\n"
			"1. View profile\n"
			"2. Edit name/major/school\n"
			"3. Add work history\n"
			"4. Edit work history\n"
			"5. Remove work history\n"
			"6. Add personal project\n"
			"7. Edit personal project\n"
			"8. Remove personal project\n"
			"9. Add award\n"
			"10. Edit award\n"
			"11. Remove award\n"
			"12. Add coursework\n"
			"13. Edit coursework\n"
			"14. Remove coursework\n"
			"15. Delete user profile\n"
			"16. Save profile\n"
			"17. Exit"
		)

		choice = input("Choose an option: ").strip()

		if choice == "1":
			show_profile(profile)
		elif choice == "2":
			old_key = user_key
			edit_basic_info(profile)
			new_key = normalized_key(profile["name"])
			if new_key != old_key and new_key in users:
				print("A profile with that name already exists. Name change not applied.")
				profile["name"] = users[old_key]["name"]
			else:
				users[new_key] = users.pop(old_key)
				user_key = new_key
			save_users(users)
		elif choice == "3":
			profile.setdefault("work_history", []).append(collect_work_history_entry())
			save_users(users)
		elif choice == "4":
			edit_work_entry(profile)
			save_users(users)
		elif choice == "5":
			remove_work_entry(profile)
			save_users(users)
		elif choice == "6":
			profile.setdefault("personal_projects", []).append(collect_personal_project_entry())
			save_users(users)
		elif choice == "7":
			edit_personal_project_entry(profile)
			save_users(users)
		elif choice == "8":
			remove_personal_project_entry(profile)
			save_users(users)
		elif choice == "9":
			profile.setdefault("awards", []).append(collect_award_entry())
			save_users(users)
		elif choice == "10":
			edit_award_entry(profile)
			save_users(users)
		elif choice == "11":
			remove_award_entry(profile)
			save_users(users)
		elif choice == "12":
			if has_attended_school(profile):
				profile.setdefault("coursework", []).append(collect_coursework_entry())
				save_users(users)
			else:
				print("Schooling not listed. Add school information first to add coursework.")
		elif choice == "13":
			if has_attended_school(profile):
				edit_coursework_entry(profile)
				save_users(users)
			else:
				print("Schooling not listed. Add school information first to edit coursework.")
		elif choice == "14":
			if has_attended_school(profile):
				remove_coursework_entry(profile)
				save_users(users)
			else:
				print("Schooling not listed. Add school information first to remove coursework.")
		elif choice == "15":
			confirm = input("Type DELETE to confirm removing this user: ").strip()
			if confirm == "DELETE":
				deleted_name = users[user_key].get("name", "user")
				users.pop(user_key)
				save_users(users)
				print(f"Deleted profile for {deleted_name}.")
				break
			print("Delete cancelled.")
		elif choice == "16":
			save_users(users)
			print("Saved profile to users.json")
		elif choice == "17":
			save_users(users)
			print("Goodbye.")
			break
		else:
			print("Invalid option.")


def pick_or_create_user(users: dict[str, dict[str, Any]]) -> str:
	print("Existing users detected:")
	for i, profile in enumerate(users.values(), start=1):
		print(f"{i}. {profile.get('name', 'Unknown')} ")

	print("Type a name to open a user, or type NEW to create one.")
	while True:
		selected = ask_non_empty("Selection: ")
		if selected.lower() == "new":
			profile = create_basic_profile()
			key = normalized_key(profile["name"])
			if key in users:
				print("That user already exists. Opening existing profile instead.")
				return key
			users[key] = profile
			save_users(users)
			print("Created new profile from basic info.")

			add_work = input("Would you like to add a work history entry (y/n): ").strip().lower()
			if add_work == "y":
				print("\nNow let's add your work history.")
				profile["work_history"] = collect_work_histories()
				save_users(users)
				print("Work history saved.")
			else:
				profile["work_history"] = []
				save_users(users)
				print("Work history skipped.")

			add_project = input("Would you like to add a personal project (y/n): ").strip().lower()
			if add_project == "y":
				print("\nNow let's add your personal projects.")
				profile["personal_projects"] = collect_personal_projects()
				save_users(users)
				print("Personal projects saved.")
			else:
				profile["personal_projects"] = []
				save_users(users)
				print("Personal projects skipped.")

			add_award = input("Would you like to add an award or recognition (y/n): ").strip().lower()
			if add_award == "y":
				print("\nNow let's add your awards.")
				profile["awards"] = collect_awards()
				save_users(users)
				print("Awards saved.")
			else:
				profile["awards"] = []
				save_users(users)
				print("Awards skipped.")

			if has_attended_school(profile):
				add_coursework = input("Would you like to add coursework (y/n): ").strip().lower()
				if add_coursework == "y":
					print("\nNow let's add your coursework.")
					profile["coursework"] = collect_coursework()
					save_users(users)
					print("Coursework saved.")
				else:
					profile["coursework"] = []
					save_users(users)
					print("Coursework skipped.")
			else:
				profile["coursework"] = []
				save_users(users)
				print("Coursework skipped because no schooling was provided.")
			return key

		key = normalized_key(selected)
		
		if key in users:
			return key
		print("No user found with that name. Try again or type NEW.")


def main() -> None:
	users = load_users()

	if not users:
		print("No existing users found. Starting full profile setup.")
		profile = create_basic_profile()
		key = normalized_key(profile["name"])
		users[key] = profile
		save_users(users)
		print("Basic profile created.")

		add_work = input("Would you like to add a work history entry (y/n): ").strip().lower()
		if add_work == "y":
			print("\nNow let's add your work history.")
			profile["work_history"] = collect_work_histories()
			save_users(users)
			print("Work history saved.")
		else:
			profile["work_history"] = []
			save_users(users)
			print("Work history skipped.")

		add_project = input("Would you like to add a personal project (y/n): ").strip().lower()
		if add_project == "y":
			print("\nNow let's add your personal projects.")
			profile["personal_projects"] = collect_personal_projects()
			save_users(users)
			print("Personal projects saved.")
		else:
			profile["personal_projects"] = []
			save_users(users)
			print("Personal projects skipped.")

		add_award = input("Would you like to add an award or recognition (y/n): ").strip().lower()
		if add_award == "y":
			print("\nNow let's add your awards.")
			profile["awards"] = collect_awards()
			save_users(users)
			print("Awards saved.")
		else:
			profile["awards"] = []
			save_users(users)
			print("Awards skipped.")

		if has_attended_school(profile):
			add_coursework = input("Would you like to add coursework (y/n): ").strip().lower()
			if add_coursework == "y":
				print("\nNow let's add your coursework.")
				profile["coursework"] = collect_coursework()
				save_users(users)
				print("Coursework saved.")
			else:
				profile["coursework"] = []
				save_users(users)
				print("Coursework skipped.")
		else:
			profile["coursework"] = []
			save_users(users)
			print("Coursework skipped because no schooling was provided.")
		existing_user_menu(users, key)
		return

	selected_key = pick_or_create_user(users)
	existing_user_menu(users, selected_key)

	return selected_key


if __name__ == "__main__":
	main()
