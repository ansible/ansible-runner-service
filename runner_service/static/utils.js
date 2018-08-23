
function showme() {

    var tr = this;

    // if data is selected, the user is trying to copy text so simply
    // exit
    var selection_type = window.getSelection().type;
    if (selection_type == "Range") {
        return;
    }

    var td = this.getElementsByTagName("td")[0];
    details = td.getElementsByTagName("div")[0];
    details.style.display = details.style.display === 'none' ? 'inline-block' : 'none';

}
