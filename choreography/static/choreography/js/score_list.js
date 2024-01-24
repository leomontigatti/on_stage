var mediaRecorder
var audio
var playPromise
var blob
var _submitButton
var alertModal

function disableButtons() {
    const buttons = document.querySelectorAll("button")
    if (buttons) {
        for (var btn of buttons) {
            btn.disabled = true
        }
    }

    const anchors = document.querySelectorAll("a")
    if (anchors) {
        for (var anchor of anchors) {
            anchor.classList.add("disabled")
        }
    }
}

function enableButtons() {
    const buttons = document.querySelectorAll("button")
    if (buttons) {
        for (var btn of buttons) {
            btn.disabled = false
        }
    }

    const anchors = document.querySelectorAll("a")
    if (anchors) {
        for (var anchor of anchors) {
            anchor.classList.remove("disabled")
        }
    }
}

function getStopRecordingButtonString(button) {
    const idIndex = button.id.indexOf("_")
    const scoreId = button.id.substring(0, idIndex)

    const stopIcon = document.createElement("i")
    stopIcon.classList.add("bi", "bi-stop-fill", "me-2")
    const stopButton = document.createElement("button")
    stopButton.type = "button"
    stopButton.id = `${scoreId}_stop`
    stopButton.classList.add("btn", "btn-outline-secondary", "rounded-pill")
    stopButton.setAttribute("onclick", "stopRecording(this)")
    stopButton.append(stopIcon, "Stop")
    return stopButton.outerHTML
}

function getPlayButtonString(button) {
    const idIndex = button.id.indexOf("_")
    const scoreId = button.id.substring(0, idIndex)
    const isLocked = "isLocked" in button.dataset

    // Get current URL
    const origin = window.location.origin

    //Play button
    const playIcon = document.createElement("i")
    playIcon.classList.add("bi", "bi-play-fill", "me-2")
    const playButton = document.createElement("button")
    playButton.type = "button"
    playButton.id = `${scoreId}_play`

    if (isLocked) {
        playButton.classList.add("btn", "btn-outline-primary", "rounded-pill")
        playButton.dataset.isLocked = ""
    } else {
        playButton.classList.add("btn", "btn-outline-primary", "rounded-start-pill")
    }

    playButton.dataset.url = button.dataset.url
    playButton.setAttribute("onclick", "playAudio(this)")
    playButton.append(playIcon, "Play")

    // Delete button
    const deleteIcon = document.createElement("i")
    deleteIcon.classList.add("bi", "bi-trash3-fill", "ms-2")
    const deleteButton = document.createElement("a")
    deleteButton.href = `${origin}/score/delete_feedback/${scoreId}${window.location.search}`
    deleteButton.id = `${scoreId}_delete`
    deleteButton.classList.add("btn", "btn-outline-danger", "rounded-end-pill")
    deleteButton.append("Delete", deleteIcon)

    // Button group
    const buttonGroup = document.createElement("div")
    buttonGroup.classList.add("btn-group")
    buttonGroup.appendChild(playButton)
    buttonGroup.appendChild(deleteButton)

    if (isLocked) {
        return playButton.outerHTML
    } else {
        return buttonGroup.outerHTML
    }
}

function getStopButtonString(button) {
    const idIndex = button.id.indexOf("_")
    const scoreId = button.id.substring(0, idIndex)
    const url = button.dataset.url
    const isLocked = "isLocked" in button.dataset

    const stopIcon = document.createElement("i")
    stopIcon.classList.add("bi", "bi-stop-fill", "me-2")
    const stopButton = document.createElement("button")
    stopButton.type = "button"
    stopButton.id = `${scoreId}_stop`
    stopButton.classList.add("btn", "btn-outline-secondary", "rounded-pill")
    stopButton.setAttribute("onclick", "pauseAudio(this)")
    stopButton.dataset.url = url

    if (isLocked) {
        stopButton.dataset.isLocked = ""
    }

    stopButton.append(stopIcon, "Stop")
    return stopButton.outerHTML
}

function startRecording(button) {
    if (!getSubmitButton(button)) return

    const parentTd = button.parentElement

    disableButtons()

    // Replace button
    parentTd.innerHTML = getStopRecordingButtonString(button)

    if (navigator.mediaDevices.getUserMedia) {
        let onSuccess = function(stream) {
            mediaRecorder = new MediaRecorder(stream)
            mediaRecorder.start()
        }

        let onError = function(err) {
            console.log('The following error occurred: ' + err)
        }

        navigator.mediaDevices.getUserMedia({audio: true}).then(onSuccess, onError)
    }
}

function stopRecording(button) {
    const parentTd = button.parentElement

    enableButtons()

    // Replace button
    parentTd.innerHTML = getPlayButtonString(button)

    let audioData = []

    mediaRecorder.stop()

    mediaRecorder.onstop = function(e) {
        blob = new Blob(audioData, {type: "audio/ogg; codecs=opus"})
        const audioURL = window.URL.createObjectURL(blob)

        const playButton = parentTd.querySelector("[id$='_play']")
        playButton.dataset.url = audioURL
        getSubmitButton(button)
    }

    mediaRecorder.ondataavailable = function(e) {
        audioData.push(e.data)
    }
}

function playAudio(button) {
    const parentTd = button.parentElement

    var url = button.dataset.url
    audio = new Audio(url)
    playPromise = audio.play()

    audio.onplay = function(e) {
        disableButtons()
        // Replace button
        parentTd.innerHTML = getStopButtonString(button)
    }

    audio.onended = function(e) {
        enableButtons()
        // Replace button
        parentTd.innerHTML = getPlayButtonString(button)
    }
}

function pauseAudio(button) {
    const parentTd = button.parentElement

    if (playPromise !== undefined) {
        playPromise.then(function() {
            audio.pause()
        })
        .catch(function(error) {
            console.log(error)
        })
    }
    // Replace button
    parentTd.innerHTML = getPlayButtonString(button)

    enableButtons()
}

function submitForm(button) {
    const scoreId = button.id.split("_")[0]
    const form = document.getElementById(`${scoreId}_form`)

    const formData = new FormData(form)

    if (blob) {
        formData.append("score_feedback", blob)
    }

    // Get current URL
    const url = window.location.href
    fetch(url, {
        method: "POST",
        mode: "no-cors",
        body: formData,
    }).then(response => {
        console.log('response')
        console.log(response)
        if (response.status === 200) {
            window.location.replace(url)
        }
    })
    .catch(e => {
        console.log('error')
        console.log(e)
    })
}

function getSubmitButton(element) {
    const scoreId = element.id.split("_")[0]
    const actionsSpan = document.getElementById(`${scoreId}_actions`)
    var submitButton = document.getElementById(`${scoreId}_submit`)

    if (_submitButton && _submitButton != submitButton) {
        // Show modal if a submit button already exists.
        if (!alertModal) {
            alertModal = new bootstrap.Modal(document.getElementById("alertModal"), {})
        }
        alertModal.show()
        return false
    } else if (!submitButton) {
        submitButton = document.createElement("button")
        submitButton.type = "button"
        submitButton.id = `${scoreId}_submit`
        submitButton.setAttribute("onclick", "submitForm(this)")
        submitButton.classList.add("btn", "btn-success", "rounded-circle")
        submitButton.dataset.bsToggle = "tooltip"
        submitButton.dataset.bsTitle = "Save"
        submitButton.innerHTML = '<i class="bi bi-check-lg"></i>'

        _submitButton = submitButton
        actionsSpan.prepend(submitButton)
    }
    return true
}
