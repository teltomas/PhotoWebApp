
/* function to toggle images selection on */
function toggleTrue(element) {
    var checkboxes = document.getElementsByName(element);
    
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked == false)
            checkboxes[i].checked = true;
    }

}

/* function to toggle images selection of */
function toggleFalse(element) {
    var checkboxes = document.getElementsByName(element);
    
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked == true)
            checkboxes[i].checked = false;
    }

}

/* function to fill array of images to delete and activate confirm deletion button */
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

/* function to fill array of images to remove from gallery and submit command */
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

/* function to fill array of images to add to gallery and submit command */
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

/* function update the copyright date in page footer as years go by */
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

/* function to open and close nav menu in small viewports */
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

/* function to two step delete confirmation */
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

/* function for management change password conditions validation */
function passvalidation() {

    document.querySelector('npass', 'repass'),addEventListener('keyup', function ValidatePassword() {

        let newPass = document.getElementById('npass').value;
        let newPassRepeat= document.getElementById('repass').value;

        let intCount = 0;
        let validation = false;
        let match = false;

        for (let i in newPass) {
            if (newPass[i] >= '0' && newPass[i] <= '9') {
                intCount++;
                }
        }

        if (intCount > 0 && intCount != newPass.length && newPass.length > 7) {

            document.getElementById('passvalidation').innerHTML = "OK";
            validation = true;

        }
        else {

            document.getElementById('passvalidation').innerHTML = "New password does not meet the requirements";
            document.getElementById('passupdate').disabled = true;
            validation = false;

        }

        if (newPass == newPassRepeat) {

            document.getElementById('repassvalidation').innerHTML = "";
            match = true;
        
        }
        else {

            document.getElementById('repassvalidation').innerHTML = "Passwords don't match";
            document.getElementById('passupdate').disabled = true;
            match = false;

        }

        if (validation && match) {

            document.getElementById('passupdate').disabled = false; 
            document.getElementById('repassvalidation').innerHTML = "OK";

        }

        if (newPass.length == 0) {

            document.getElementById('passvalidation').innerHTML = "";
        
        }

    });
}