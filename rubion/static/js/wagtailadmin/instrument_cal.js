window.rubion = {
    calendar : {
	start : '',
	end : '',
	get_start_date : function( field ){
	    return $(field).parents('table').data('day')+' '+$(field).data('start-time');
	},
	get_end_date : function( field ){
	    return $(field).parents('table').data('day')+' '+$(field).data('end-time');
	}
    }
}

function createInstrumentCalModal() {
    console.log('Running...');
    var btns = $('.instrument-cal-btn');
    console.log('N buttons is: '+btns.length);
    btns.click(
	function( evt ){
	    var r_url = $(this).attr('href');
	    console.log($(this)+' was clicked.');
	    evt.preventDefault();
	    ModalWorkflow({
		url : r_url,
		responses : {
		    
		}
	    });
	    return false;
	}
    );
}

$( document ).ready(createInstrumentCalModal);

