(function (root, factory) {
    if ( typeof define === 'function' && define.amd ) {
	define([], factory(root));
    } else if ( typeof exports === 'object' ) {
	module.exports = factory(root);
    } else {
	root.doi = factory(root);
    }
})(typeof global !== 'undefined' ? global : this.window || this.global, function (root) {
    
    'use strict';
    
    //
    // Variables
    //
    
    var DOIRegExp = new RegExp('^(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![%"#? ])\\S)+)$');

    var doi = {}; // Object for public APIs
    var basic_url = 'https://data.crossref.org/'
    var doi_field;
    var fields = {};
    var checkDOI = function( doi ){
	return DOIRegExp.exec( doi );
    };
    var request;
    var get_initials = function(first_name){
	var parts = first_name.split(" ");
	var ret = '';
	for (var i=0; i<parts.length; i++){
	    ret += parts[i][0];
	}
	return ret;
    };

    var parse_authors = function(authors){
	var author_string;
	if (authors.length == 1){
	    author_string = authors[0].family +" "+ get_initials(authors[0].given);
	} else if (authors.length == 2){
	    author_string = authors[0].family + " "+get_initials(authors[0].given);
	    author_string += ' & '+authors[1].family + " "+get_initials(authors[1].given);
	} else {
	    author_string = authors[0].family + " "+get_initials(authors[0].given)+' et al.';
	}
	return author_string;
	
    }
    var update_fields = function(){
	if( request.status >= 200 && request.status < 300){
	    var result = JSON.parse(request.response);
	    document.getElementById(fields['title']).value = result['title'];
	    document.getElementById(fields['author']).value = parse_authors(result['author']);
	    document.getElementById(fields['journal']).value = result['container-title-short'] || result['container-title'];
	    document.getElementById(fields['volume']).value = result['volume'] || '';
	    document.getElementById(fields['pages']).value = result['page'] || result['article-number'] || '';
	    var year = '';
	    if (result['published-print']){
		year = result['published-print']['date-parts'][0][0];
	    }
	    else if (result['published-online']) {
		year = result['published-online']['date-parts'][0][0];
	    }
	    else if (result['created']) {
		year = result['created']['date-parts'][0][0];
	    }
    
	    document.getElementById(fields['year']).value =  year;
	}
	else {
	    console.warn(request.status);
	}
    }
    var fetch_doi = function( doi ){
	request = new XMLHttpRequest();
	request.addEventListener('load',update_fields);
	request.open('GET', basic_url+ doi);
	request.setRequestHeader('Accept','application/vnd.citationstyles.csl+json;q=1.0');
	request.send();
    };
    var solve_doi = function(){
	var _doi = doi_field.value.trim();
	if (checkDOI( _doi )){
	    fetch_doi( _doi );
	}
	else {
	    console.log('Not a valid DOI');
	}
    }
    doi.init = function(doi_field_id, resolved_fields){
	fields = resolved_fields;
	doi_field = document.getElementById(doi_field_id);
	doi_field.addEventListener("change", solve_doi);
    }
    return doi;

});
