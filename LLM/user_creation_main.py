from Interview_algor import load_users, main, save_users
from LLM_interviewer import work_prompt_creation
from LLM_rewriter import LLM_revision_main


#------- functions -------
def handle_follow_up_answers(job: dict) -> list[str] | None:
    existing_answers = job.get("follow_up_answers", [])
    title = job.get("title", "No title")

    if existing_answers:
        print(f"\nJob: {title}")
        print("This job already has follow-up answers saved.")
        print("1. Skip this job")
        print("2. Overwrite follow-up answers")
        print("3. View existing follow-up answers")

        while True:
            choice = input("Choose an option: ").strip()
            if choice == "1":
                return
            if choice == "2":
                break
            if choice == "3":
                print("Existing follow-up answers:")
                for index, answer in enumerate(existing_answers, start=1):
                    print(f"{index}. {answer}")
                continue
            print("Invalid option.")

    follow_up_answers = work_prompt_creation(
        job.get("title", "No title"),
        job.get("duration", "No duration"),
        job.get("duties", ""),
        job.get("feelings", ""),
    )

    # adding follow up entries to users profile
    # this will be stored underneith the job title associated
    return follow_up_answers




# ---------- main execution -----------
# this runs the main interview algorithm
user_name = main()

# reload after main so we see any edits made during the profile flow
users = load_users()

#this aquries the data related to the typed user
user_data = users.get(user_name)

if user_data is None:
    raise KeyError(f"Could not find user profile for {user_name!r}")

print("\nNow I will begin to ask some follow up questions in regard to your work history... ")

for i, job in enumerate(user_data.get("work_history",[]),start=1):
    title = job.get("title", "No title")
    duration = job.get("duration", "No duration")
    duties = job.get("duties", "")
    feelings = job.get("feelings", "")

    print("May I ask some follow up question on...")
    print(f"Job #{i}: {title} ({duration})")
    user_input = input("Type (Y or N): ").strip().upper()

    if user_input == "Y":
        QA_answers = handle_follow_up_answers(job)

        if QA_answers is not None:
            job["follow_up_answers"] = list(QA_answers)
            LLM_job_posting_revision = LLM_revision_main(title, duration, duties, feelings, QA_answers)
            job["AI_REVISON"] = LLM_job_posting_revision
        else:
            print('moving onto the next job posting')

    
save_users(users)
