import whisper

model = whisper.load_model("turbo", device="cpu")
result = model.transcribe("/path/to/audio/file/",
                          fp16=False)
print(result["text"])
