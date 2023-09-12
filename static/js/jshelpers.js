/*! getEmPixels  | Author: Tyson Matanich (http://matanich.com), 2013 | License: MIT */
(function(n,t){"use strict";var i="!important;",r="position:absolute"+i+"visibility:hidden"+i+"width:1em"+i+"font-size:1em"+i+"padding:0"+i;window.getEmPixels=function(u){var f,e,o;return u||(u=f=n.createElement("body"),f.style.cssText="font-size:1em"+i,t.insertBefore(f,n.body)),e=n.createElement("i"),e.style.cssText=r,u.appendChild(e),o=e.clientWidth,f?t.removeChild(f):u.removeChild(e),o}})(document,document.documentElement);


// This is a JS implementation of the PHP function `wordwrap()`
//
// @param {string} str
// @param {number} width
// @param {string} breakStr
// @param {boolean} cut
// @return {string}
function wordwrap(str, width, breakStr, cut) {
  if (str == null) {
	return '';
  }
  let regex = '(.{1,' + width + '})( +|$\n?)|(.{1,' + width + '})';
  return str.match(new RegExp(regex, 'g')).join(breakStr || '\n');
}

// Function for setting the cookie
function setCookie(cname, cvalue) {
	document.cookie = cname + "=" + encodeURIComponent(cvalue) + ";path=/;SameSite=Lax";
}
function getCookie(cname) {
	let name = cname + "=";
	let decodedCookie = decodeURIComponent(document.cookie);
	let ca = decodedCookie.split(';');
	for(let i = 0; i <ca.length; i++) {
		let c = ca[i];
		while (c.charAt(0) == ' ') {
			c = c.substring(1);
		}
		if (c.indexOf(name) == 0) {
			return c.substring(name.length, c.length);
		}
	}
	return null;
}


function deleteAllCookies() {
	console.log(document.cookie)
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i];
        const eqPos = cookie.indexOf("=");
        const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
}

function sendDataGet(data_dict){
	data_dict["js_req"] = true;
	$.ajax({
          url: '/update_game_session',
          data: data_dict,
          dataType: 'json'
      });
}

function setMessageLevel(level){
	if(level=="DEBUG"){
		sendDataGet({"set_message_level":10})
	}
	else if(level=="INFO"){
		sendDataGet({"set_message_level":20})
	}
	else if(level=="WARNING"){
		sendDataGet({"set_message_level":30})
	}
	else if(level=="ERROR"){
		sendDataGet({"set_message_level":40})
	}
	else{
		return "Unknown level"
	}
	return "success"
}

function clearAll(){
    sendDataGet({"clear_everything":true})
}

function compareNumbersWrapped(a, b)
{
  return a[0] - b[0];
}
function getDictValues(dic){
    let dicNew = Object.keys(dic).map(function(key){
        return dic[key];
      });
    return dicNew
}
function getSortIndices(dic, reverse=false){
    if(dic.constructor.name != "Array"){
       dic = getDictValues(dic)
    }
  let sortKeys=a=>a.map((v,i)=>[v,i]).sort(compareNumbersWrapped).map(i=>i[1])
  if(reverse==true){
    return sortKeys(dic).reverse()
  }
  else{
    return sortKeys(dic)
  }
}


function sortByIndices(arr,indices){
    if(arr.constructor.name != "Array"){
        let newDic = {}
        let keys = Object.keys(arr)
        for(let i in indices){
          newDic[keys[indices[i]]] =  arr[keys[indices[i]]]
        }
        return newDic
    }
    else{
      let newArr = []
      for(let i in indices){
        newArr.push(arr[indices[i]])
      }
      return newArr
    }
}
