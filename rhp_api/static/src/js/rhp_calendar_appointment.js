$( document ).ready(function() {
    if (document.getElementById('month_2') !=null) {
        document.getElementById('month_2').style.display = 'none';
    }
    else {
        var nexts = document.getElementsByClassName('btn_next'); 
        for (var i=0;i<nexts.length;i+=1){
            nexts[i].style.display = 'none';
        }
    }
});