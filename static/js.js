
function toggleTrue(element) {
    var checkboxes = document.getElementsByName(element);
    
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked == false)
            checkboxes[i].checked = true;
    }

}

function toggleFalse(element) {
    var checkboxes = document.getElementsByName(element);
    
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked == true)
            checkboxes[i].checked = false;
    }

}

function toggleSwitch(element) {
    var checkboxes = document.getElementsByName(element);
    
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked == true) {
            checkboxes[i].checked = false;
        }
        else if (checkboxes[i].checked == false) {
                checkboxes[i].checked = true;
            }
    }
}

function confdel() {

    var checkboxes = document.getElementsByName("imgselect");

    imgids = []

    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked == true) {
            imgids.push(checkboxes[i].value)
        }
    } 

    if ((document.querySelector('#delbtn').style.display == "none") && imgids.length > 0) {

        document.querySelector('#delbtn').style.display = "block";

        document.querySelector('#imgsarray').value = imgids;
        console.log(imgids);

    }
    else {
        document.querySelector('#delbtn').style.display = "none";
        imgids = null;
    }
}

function rmvImgs() {

    var checkboxes = document.getElementsByName("gallsel");

    imgids = []

    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked == true) {
            imgids.push(checkboxes[i].value)
        }
    } 

    if (imgids.length > 0) {

        document.querySelector('#imgrmvid').value = imgids;
        console.log(imgids);

        document.getElementById("gallrmv").submit();

    }
}

function addImgs() {

    var checkboxes = document.getElementsByName("addselect");

    imgids = []

    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked == true) {
            imgids.push(checkboxes[i].value)
        }
    } 

    if (imgids.length > 0) {

        document.querySelector('#imgaddid').value = imgids;
        console.log(imgids);

        document.getElementById("galladd").submit();

    }
}

