// CJK fix for open-edit captions. Copy beside the page and load it right after captions.js.
// captions.js puts a space text node between every two words, so Chinese shows as「视 频」.
// cjk-captions.css makes each line a flex row, which drops those whitespace-only nodes;
// this file then puts back the spaces that belong: between two Latin words ("Claude Code")
// and between Chinese and Latin ("用 Claude"), as a no-break space inside the word itself.
(function () {
  if (!window.openeditCaptions) return;
  var ALNUM_END = /[A-Za-z0-9%+#]$/;
  var ALNUM_START = /^[A-Za-z0-9$#@]/;
  var CJK_END = /[㐀-鿿豈-﫿]$/;
  var CJK_START = /^[㐀-鿿豈-﫿]/;
  var words = window.openeditCaptions.words();
  for (var i = 0; i < words.length - 1; i++) {
    var a = words[i].text, b = words[i + 1].text;
    var gap = (ALNUM_END.test(a) && (ALNUM_START.test(b) || CJK_START.test(b)))
      || (CJK_END.test(a) && ALNUM_START.test(b));
    if (gap) words[i].text = a + '\u00a0';
  }
})();
