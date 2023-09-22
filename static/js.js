
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

function footeryear() {
    curryear = new Date().getFullYear();
    if (document.getElementById("year").textContent != curryear)
        document.getElementById("currentyear").innerHTML = " - " + new Date().getFullYear();
}

/* email validation function as shown here: */
/*https://www.simplilearn.com/tutorials/javascript-tutorial/email-validation-in-javascript*/

function emailvalidation () {
    document.querySelector('email'),addEventListener('keypress', function ValidateEmail() {

        var validRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;

        input = document.getElementById("email");
      
        if (input.value.match(validRegex)) {
      
            document.getElementById("valwarning").style.visibility = "hidden";
            document.getElementById("submitbttn").disabled = false;
      
          return true;
      
        } else {
      
            document.getElementById("valwarning").style.visibility = "visible";
            document.getElementById("submitbttn").disabled = true;
      
          return false;
      
        }
      
      });
}

function openclose() {

    let status = document.getElementById("menulist").style.display;

    if (status == "none") {

        document.getElementById("menulist").style.display = "block";
        document.getElementById("container").style.opacity = "0.2";

    } else {

        document.getElementById("menulist").style.display = "none";
        document.getElementById("container").style.opacity = "1";

    }

}

function deltoggle() {

    let status = document.getElementById("confirmdel").style.display;

    if (status == "none") {

        document.getElementById("confirmdel").style.display = "block";
        document.getElementById("cancel").style.display = "block";

    } else {

        document.getElementById("confirmdel").style.display = "none";
        document.getElementById("cancel").style.display = "none";

    }

}