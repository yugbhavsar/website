$R  = {
    show_spinner: function(elem){
	var e = document.getElementById(elem);
	var spinner = document.createElement('div');
	spinner.setAttribute('class','spinner');
	e.innerHTML='';
	e.appendChild(spinner);
    },
    hide_spinner: function(elem){
	var e = document.getElementById(elem);
	var spinner = e.getElementsByClassName('spinner');
	for (var i=0; i < spinner.length; ++i){
	    e.removeChild(spinner[i]);
	}
    }
};
$R.pubs = {
    get_pubs_by_year: function( elem, year, range ){
	var style = "perspectives";
	var url =  [
	    "https://bibliographie.ub.rub.de/beta/chair/16062416-2/bibliography",
	    style 
	];
	
	var e = document.getElementById(elem);
	$R.show_spinner(elem);
	responses = {};
	call = function(thisyear){
	    var options = {
		//	    'filter_by_pr' : true,
		'filter_by_year' : thisyear,
		'format' : 'html'
	    }
	    var req_url = [
		url.join('/'),
		Object.keys(options).map(
		    function( key ){
			return key + '=' + options[key];
		    }
		).join('&')
	    ].join('?');
	    req = new XMLHttpRequest();
	    req.open( "GET", req_url );
	    req.addEventListener( 'load', function(event) {
		if ( ( req.status >= 200 && req.status < 300 ) || req.status == 304) {
		    responses[thisyear] = req.responseText;
		    if (thisyear - 1 > year - range){
			call(thisyear-1);
		    }
		    else{
			update_html();
		    }
		} else {
		    console.warn( req.statusText, req.responseText );
		}
	    });
	    req.send();
	}

	call(year);

	update_html = function(){
	    nav = get_navigation();
	    HTML = nav;
	    HTML += '<h3>'+year+'–'+(year-range+1)+'</h3>';

	    var keys = [];
	    for ( k in responses ) {
		if ( responses.hasOwnProperty(k) ) {
		    keys.push(k);
		}
	    }
	    
	    keys.sort();


	    for (var i =  keys.length-1; i >= 0; --i){
		k = keys[i];
		HTML += '<h3>'+k+'</h3>\n';
		HTML += responses[k]
	    }
	    HTML += nav;
	    e.innerHTML = HTML;
	    $R.hide_spinner(elem);
	}
	get_navigation = function(){
	    r = '<nav>';
	    
	    if (year < new Date(Date.now()).getFullYear() ){
		r+='<button class="newer" onclick="$R.pubs.get_pubs_by_year(\'publication_list\', '+(year+range)+','+range+')"><span class="icon">◀</span><span class="text">'+(year+range)+'–'+(year+1)+'</span></button>';
	    }
	    else {
		r+='<button class="disabled"><span class="icon">◀</span><span class="text">'+(year+range)+'–'+(year+1)+'</span></button>';
	    }
	    r += '</td><td>';
	    if (year - range > 1969){
		r+='<button class="older" onclick="$R.pubs.get_pubs_by_year(\'publication_list\', '+(year-range)+','+range+')"><span class="text">'+(year-range)+'–'+(year-2*range+1)+'</span><span class="icon">▶</span></button>';
	    }
	    return r + '</nav>';
	}
    },
    
}


window.onload = function(){
    $R.pubs.get_pubs_by_year('publication_list', new Date(Date.now()).getFullYear(), 3);
}
    
