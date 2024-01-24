let choreographiesIdList = []
const selectedChoreographiesId = document.getElementById('selected_choreographies_id')
let depositAmountTotal = 0
const depositAmountTotalId = document.getElementById('deposit_amount')
let balanceAmount = 0
const balanceAmountId = document.getElementById('balance_amount')

function checkAll(source) {
    const checkboxes = document.getElementsByName('_selected_action')
    for (let i = 0, n = checkboxes.length; i < n; i++) {
        if (checkboxes[i].checked != source.checked) {
            checkboxes[i].checked = source.checked
            setSelected(checkboxes[i])
        }
    }
}

function setSelected(element) {
    const selectedTr = document.getElementById(element.value + '_tr')
    const depositAmount = selectedTr.querySelector('td[name="deposit_amount"]').innerText
    const balancePrice = selectedTr.querySelector('td[name="balance_price"]').innerText
    const depositPaid = selectedTr.querySelector('img[name="deposit_paid"]').alt

    if (element.checked) {
        selectedTr.classList.add('selected')
        if (depositPaid === 'True') {
            balanceAmount += parseFloat(balancePrice)
        } else if (depositPaid === 'False') {
            depositAmountTotal += parseFloat(depositAmount)
            balanceAmount += parseFloat(balancePrice)
        }
        choreographiesIdList.push(element.value)
    } else {
        selectedTr.classList.remove('selected')
        if (depositPaid === 'True') {
            balanceAmount -= parseFloat(balancePrice)
        } else if (depositPaid === 'False') {
            depositAmountTotal -= parseFloat(depositAmount)
            balanceAmount -= parseFloat(balancePrice)
        }
        choreographiesIdList.splice(choreographiesIdList.indexOf(element.value), 1)
    }
    depositAmountTotalId.innerHTML = '$ <b>' + depositAmountTotal + '</b>'
    balanceAmountId.innerHTML = '$ <b>' + balanceAmount + '</b>'
    selectedChoreographiesId.value = choreographiesIdList
}
