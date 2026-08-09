from ollama import chat

# variables needed
MODEL = "llama3.2:3b"

system_prompt_2 = '''
you are to rewirte the work history paragraph as if the user work history is a job posting, for example, if a user were to tell you their experince as a teacher
    then you rewrite it in a way that sounds like this: 
    
MINIMUM QUALIFICATIONS:

Bachelor’s Degree from an accredited institution of higher education.
Valid Texas Teaching Certificate with required endorsements for subject/level assigned. Must be ESL certified.
Must possess strong communication and writing skills.
Must pass a background check.
POSITION DESCRIPTION:

Core Instructional Responsibilities

Implements and teaches a challenging curriculum that addresses the current academic levels of elementary school students
Develops and implements elementary school lesson plans that effectively meet the needs of students with various learning styles
Plans and uses appropriate instructional and learning strategies, activities, materials and equipment that reflects an understanding of the learning styles and needs of assigned students
Conducts ongoing assessment of student achievement through formal and informal testing
Conducts assessments of student learning styles and uses the results to plan instructional activities and inform instructional decisions
Creates a classroom environment conducive to learning and appropriate for the physical, social and emotional development of students
Manages student behavior in accordance with the Student Code of Conduct and student handbook
Core Professional Responsibilities

Keeps informed of and complies with applicable federal, state and school regulations and policies for classroom teachers

Establishes and maintains openness of communication by conducting conferences with parents, students, principals and teachers to discuss the progress of students
Enforces and upholds the school's values, policies, and culture
Models the school's values in all interactions with students, families, community members, and faculty
Works collaboratively with staff members and participates in staff development activities
Pursues and engages in opportunities for professional growth
Maintain regular and reliable attendance
Other Professional Responsibilities

Serves as an advisor to a group of students, as assigned
Performs additional duties and accepts other responsibilities as may be assigned
WORKING CONDITIONS/PHYSICAL DEMANDS

May be required to work more than 40 hours during the workweek.

May lift 5–10 pounds frequently, 10–50 pounds occasionally, and more than 50 pounds infrequently. 
Must maintain emotional control under stress. Moderate walking, standing, stooping, kneeling, bending, twisting. 
May work indoors and outdoors in varying climate conditions. Subject to visual acuity, speech/hearing, hand/eye coordination and manual dexterity.
'''

def LLM_revision_main(title, duration, duties, feelings, QA_answers):
    follow_up_text = "\n".join(f"- {writing}" for writing in QA_answers)
    if not follow_up_text:
        follow_up_text = "- No follow-up answers provided"

    user_work_history = (
        f"Title: {title}\n"
        f"Duration: {duration}\n"
        f"Duties: {duties}\n"
        f"Feelings: {feelings}\n"
        f"Follow-up answers:\n{follow_up_text}"
    )

    # variables needed
    MODEL = "llama3.2:3b"

    # the message or prompt we will give the model:
    messages_2 = [
        {
            "role": "system",
            "content":system_prompt_2
        },
        {
            "role": "user",
            "content":user_work_history
        },
    ]

    # this will revise the work history
    response = chat(
        model=MODEL,
        messages=messages_2,
        options={"temperature": 0.5},
    )
    revision = response["message"]["content"]
    print("")
    print('Preparing for content revision...')
    print(revision)

    return revision