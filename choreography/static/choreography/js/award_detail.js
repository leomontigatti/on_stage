const feedbackSpan = document.getElementsByName("feedback")
console.log(feedbackSpan)

if (feedbackSpan) {
    for (var span of feedbackSpan) {
        const parentTd = span.parentElement
        const url = span.innerText

        audio = new Audio(url)
        const audioElement = document.createElement("audio")
        audioElement.controls = true
        audioElement.controlsList = "nodownload"
        audioElement.src = audio.src

        parentTd.appendChild(audioElement)
    }
}
