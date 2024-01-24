const selectAllCheck = document.getElementById("select-all")
if (selectAllCheck) {
    selectAllCheck.addEventListener("click", selectAll)
}

function selectAll() {
    const dancersCheck = document.getElementsByName("dancers")
    if (this.checked) {
        for (var dancerCheck of dancersCheck) {
            dancerCheck.checked = true
        }
    } else {
        for (var dancerCheck of dancersCheck) {
            dancerCheck.checked = false
        }
    }
}
