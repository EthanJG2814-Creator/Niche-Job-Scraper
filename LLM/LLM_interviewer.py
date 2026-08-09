
from ollama import chat

# system prompt for the model
system_prompt_1= '''
You are an editor, a career coach, and a hiring manager. your task is:
1. you inquire the user about their work history. you are provided a back ground of some of the jobs they previouly worked at. your job is to ask
    more meaningful questions that could help strengthen their profile such as more quantifiable duties they did, what impacts they had, and 
    clarifying their skill set. 

Here are the questions that were already asked by the user:
Can you describe the duties and responsibilities of your job?
How did you feel about the job? Was it tiring, easy, or challenging?
What technical skills did you learn on the job and how did you use them? (such as microsoft word, power point, python)
What did you learn about people and what soft skills did you use? (such as communication, time management, problem solving)

what you should do first is reason though the questions you might have for the user, then summarize your questions at the end so the user knows what to response to. 
you only get to ask 2 questions per message. provide examples for each question so the user does not get confused. 

Here is a format of the response you should give such as follow:

Analysis of users background:
ABC

summary of questions:
1. xyz

'''

def work_prompt_creation(title, duration, duties, feelings):
    user_work_history = title + duration + duties + feelings

    # variables needed
    MODEL = "llama3.2:3b"
    MAX_ROUNDS = 2
    follow_up_answers = []

    # the message or prompt we will give the model:
    messages_1 = [
        {
            "role": "system",
            "content":system_prompt_1
        },
        {
            "role": "user",
            "content":user_work_history
        },
    ]


    # itteration of follow up quetsions 
    for round_number in range(1, MAX_ROUNDS + 1):
        response = chat(
            model=MODEL,
            messages=messages_1,
            options={"temperature": 0.5},
        )
        # temperatrure symbolizes the randomness it can generate. 

        answer = response["message"]["content"]
        print(f"\n--- Follow up Round {round_number} ---")
        print(answer)

        # Save the model's answer as part of the ongoing conversation.
        messages_1.append({
            "role": "assistant",
            "content": answer,
        })

        # In a real program, this could be user input, scraped data,
        # a database query result, or a response from another function.
        follow_up_answer = input("\nAnswer the model's question (or type 'stop'): ").strip()

        if follow_up_answer.lower() == "stop":
            break

        messages_1.append({
            "role": "user",
            "content": follow_up_answer,
        })

        follow_up_answers.append(follow_up_answer)

    return follow_up_answers
