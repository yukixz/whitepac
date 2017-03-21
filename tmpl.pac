var proxy = "SOCKS5 127.0.0.1:1080; SOCKS 127.0.0.1:1080";
var direct = "DIRECT";

var DirectNetworks = {DirectNetworks};
var DirectSuffixes = {DirectSuffixes};

var hasOwnProperty = Object.hasOwnProperty;

function convert_addr(ipchars) {
    var bytes = ipchars.split('.');
    var result = (bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | (bytes[3]);
    return result >>> 0;
}

var reIPv4 = /^\d+\.\d+\.\d+\.\d+$/;
function isIPv4(host) {
    return reIPv4.test(host);
}

function isInNets(nets, host) {
    var ip = convert_addr(host);
    for (var i = 24; i >= 8; i--) {
        var key = (ip >>> i) + '/' + (32 - i);
        if (hasOwnProperty.call(nets, key))
            return true;
    }
    return false;
}

function isSuffixes(suffixes, host) {
    var parts = host.split('.');
    var node = suffixes;
    for (var i = parts.length - 1; i >= 0; i--) {
        var part = parts[i];
        node = node[part];
        if (node === undefined)
            return false
        if (node === 1)
            return true
    }
    return false;
}

function FindProxyForURL(url, host) {
    if (isPlainHostName(host)) {
        return direct;
    }
    if (isIPv4(host)) {
        if (isInNets(DirectNetworks, host))
            return direct;
    } else {
        if (isSuffixes(DirectSuffixes, host))
            return direct;
    }
    return proxy;
}

// DEBUG CODE
// function isPlainHostName(host) {
//     return host.indexOf('.') === -1
// }
// module.exports = FindProxyForURL
