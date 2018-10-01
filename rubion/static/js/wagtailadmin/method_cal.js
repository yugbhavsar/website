function createMethodCalModal() {
    var btns = $('.method-cal-btn');
    btns.click( 
	function( evt ){
	    evt.preventDefault();
	    ModalWorkflow({
		url : $(this).attr('href'),
		responses : {
		
		}
	    });
	    return false;
	}
    );
}

$( document ).ready(createMethodCalModal);


