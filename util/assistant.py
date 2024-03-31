from openai import OpenAI
import io
import sys

client = OpenAI()

prompt = """You are an expert storyteller and extrovert conversationalist with
expert proficiency in English and <language>. Your task is to engage in a
conversation with a novice <language> speaker whose native language is English.
The conversation should flow naturally and be immersive. Feel free to tell
stories, ask the user questions, and respond to the user’s stories with your
personal experience. You will also be given the speaker's fluency level on a
scale from 1-100. Your goal should be to seamlessly slip words from <language>
into the conversation, trying to target easier words if proficiency is lower and
more complex if it is higher. The amount of English you use in the conversation
should be based on this level. For any fluency level, you should write that
percentage of language in English.

Make sure to keep the conversation engaging and natural. If the user asks about
a word or phrase in <language>, give a quick response to clarify in English, and
then continue the conversation in <language>. Each of the things that you say
should be between around 2-4 sentences, but 2 in most cases if it is unnecessary
for more. Remember to write answers in <language> when responding in <language>.

Avoid long messages in <language> as this may confuse the user. The language
model should act as a friend to have a conversation with. It should prompt the
user with various conversation topics and guide them through speaking in
<language>.

Fluency level: 20/100
Language: {language}
Your Name: {name}
Begin the conversation with a short introduction of yourself in <language>."""


def run_assistant(thread_id, name, language, wpm):
    thread = client.beta.threads.messages.list(thread_id)
    messages = [{"role": message.role, "content": message.content[0].text.value}
                for message in thread.data]
    messages.reverse()
    messages.insert(0, {"role": "system", "content":
                        prompt.format(language=language, name=name), })

    print(messages, file=sys.stderr)

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4-turbo-preview",
    )

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="assistant",
        content=chat_completion.choices[0].message.content
    )

    messages.append({"role": "system", "content": """Analyze the previous text
                     text and provide a fluency score between 1 and 100, where 1
                     represents a complete beginner and 100 represents a native
                     speaker. If the user used English excessively, remove 10
                     points from their score. Respond only with a fraction of 100, like <score>/100.

                     Pace: {pace}""".format(pace=wpm)})

    fluency_rating = client.chat.completions.create(
        messages=messages,
        model="gpt-4-turbo-preview",
    )

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="assistant",
        content=f"Fluency level: {fluency_rating.choices[0].message.content}"
    )

    return chat_completion.choices[0].message.content, fluency_rating.choices[0].message.content


def whisper_tts(text, voice="echo"):
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=text
    )

    return response.content


def whisper_stt(audio_file):
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

    return transcription.text
