function createTdAndCloneRegistration(element, newRowIndex) {
    if (element.tagName === "LABEL") {
        return
    } else {
        const clone = element.cloneNode(true)
        if (
            element.id.includes("dancer") ||
            element.id.includes("deposit_amount") ||
            element.id.includes("total_price") ||
            element.id.includes("balance")
        ) {
            const newTd = document.createElement("td")
            clone.name = clone.name.replace("__prefix__", newRowIndex)
            clone.id = clone.id.replace("__prefix__", newRowIndex)
            newTd.appendChild(clone)
            return newTd
        } else {
            clone.name = clone.name.replace("__prefix__", newRowIndex)
            clone.id = clone.id.replace("__prefix__", newRowIndex)
            clone.setAttribute("hidden", "")
            return clone
        }
    }
}

function addRegistration() {
    const registrationsTable = document.getElementById("registrations-table")
    const emptyRegistrationFormset = document.getElementById("empty-registration-formset").children
    const newRow = registrationsTable.insertRow()

    const deleteTd = document.createElement("td")
    deleteTd.innerHTML = '<a class="btn btn-outline-secondary btn-sm rounded-circle disabled"><i class="bi bi-x-lg"></i></a>'
    deleteTd.classList.add("align-middle", "text-center")
    newRow.appendChild(deleteTd)

    for (const divElement of emptyRegistrationFormset) {
        for (const e of divElement.children) {
            if (e.nodeName != "LABEL") {
                const child = createTdAndCloneRegistration(e, newRow.rowIndex - 1)
                if (child) {
                    newRow.appendChild(child)
                }
            }
        }
    }

    document.getElementById("id_seminar_registration-TOTAL_FORMS").value = registrationsTable.children.length
}
