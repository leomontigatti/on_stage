let choreographiesObject = {}
const choreographiesTable = document.getElementById('choreographiesTable')
if (choreographiesTable) {
    const newOrderNumberInputList = choreographiesTable.getElementsByTagName("input")
    if (newOrderNumberInputList) {
        for (var newOrderNumberInput of newOrderNumberInputList) {
            newOrderNumberInput.addEventListener("change", setNewOrderNumber)
            choreographiesObject[newOrderNumberInput.id] = newOrderNumberInput.value
            const choreographiesJson = document.getElementById('choreographies_json')
            choreographiesJson.value = JSON.stringify(choreographiesObject)
        }
    }
}

function setNewOrderNumber() {
    choreographiesObject[this.id] = this.value
    const choreographiesJson = document.getElementById('choreographies_json')
    choreographiesJson.value = JSON.stringify(choreographiesObject)
}

// function getPreviousSibling(node) {
//     x = node.previousSibling
//     while (x.nodeType != 1) {
//         x = x.previousSibling
//     }
//     return x
// }

// function getNextSibling(node) {
//     x = node.nextSibling
//     while (x != null && x.nodeType !=1) {
//         x = x.nextSibling
//     }
//     return x
// }

// function moveUp(element) {
//     var tableRow = element.parentNode

//     var thisChoreoOrderNumberTd = getPreviousSibling(tableRow)
//     var nextChoreoOrderNumberTd = getPreviousSibling(tableRow.parentNode).firstElementChild
//     var thisTrOrderNumber = thisChoreoOrderNumberTd.innerText
//     var nextTrOrderNumber = nextChoreoOrderNumberTd.innerText
//     thisChoreoOrderNumberTd.innerText = nextTrOrderNumber
//     nextChoreoOrderNumberTd.innerText = thisTrOrderNumber

//     while (tableRow != null) {
//         if (tableRow.nodeName == 'TR') {
//             break
//         } else {
//             tableRow = tableRow.parentNode
//         }
//     }
//     var tableBody = tableRow.parentNode
//     tableBody.insertBefore(tableRow, getPreviousSibling(tableRow))
//     setNewOrderNumber()
// }

// function moveDown(element) {
//     var tableRow = element.parentNode

//     var thisChoreoOrderNumberTd = getPreviousSibling(tableRow)
//     var nextChoreoOrderNumberTd = getNextSibling(tableRow.parentNode).firstElementChild
//     var thisTrOrderNumber = thisChoreoOrderNumberTd.innerText
//     var nextTrOrderNumber = nextChoreoOrderNumberTd.innerText
//     thisChoreoOrderNumberTd.innerText = nextTrOrderNumber
//     nextChoreoOrderNumberTd.innerText = thisTrOrderNumber

//     while (tableRow != null) {
//         if (tableRow.nodeName == 'TR') {
//             break
//         } else {
//             tableRow = tableRow.parentNode
//         }
//     }

//     var tableBody = tableRow.parentNode
//     tableBody.insertBefore(tableRow, getNextSibling(getNextSibling(tableRow)))
//     setNewOrderNumber()
// }

// function setNewOrderNumber() {
//     let choreographiesObject = {}
//     const choreographiesJson = document.getElementById('choreographies_json')
//     const choreographiesTable = document.getElementById('choreographiesTable')
//     for (var row of choreographiesTable.rows) {
//         choreographiesObject[row.firstElementChild.innerText] = row.id
//     }
//     choreographiesJson.value = JSON.stringify(choreographiesObject)
// }
