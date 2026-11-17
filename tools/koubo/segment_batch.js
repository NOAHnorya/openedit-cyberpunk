ObjC.import('Foundation'); ObjC.import('Vision'); ObjC.import('CoreImage'); ObjC.import('AppKit');
// usage: osascript -l JavaScript segment_batch.js <inDir> <outDir> <quality 0|1|2> [start] [end]
function run(argv) {
  const [inDir, outDir, q, s0, e0] = argv;
  const fm = $.NSFileManager.defaultManager;
  const names = ObjC.deepUnwrap(fm.contentsOfDirectoryAtPathError(inDir, null)).filter(n => n.endsWith('.jpg')).sort();
  const start = s0 ? parseInt(s0) : 0, end = e0 ? Math.min(parseInt(e0), names.length) : names.length;
  const ctx = $.CIContext.context; const cs = $.CGColorSpaceCreateDeviceGray();
  const req = $.VNGeneratePersonSegmentationRequest.alloc.init;
  req.qualityLevel = parseInt(q); req.outputPixelFormat = 1278226488;
  const t0 = Date.now(); let n = 0;
  for (let i = start; i < end; i++) {
    const nm = names[i];
    const ci = $.CIImage.imageWithContentsOfURL($.NSURL.fileURLWithPath(inDir + '/' + nm));
    const W = ci.extent.size.width, H = ci.extent.size.height;
    const h = $.VNImageRequestHandler.alloc.initWithCIImageOptions(ci, $({}));
    if (!h.performRequestsError($([req]), null)) continue;
    const obs = req.results.objectAtIndex(0);
    let m = $.CIImage.imageWithCVPixelBuffer(obs.pixelBuffer);
    m = m.imageByApplyingTransform($.CGAffineTransformMakeScale(W / m.extent.size.width, H / m.extent.size.height));
    ctx.writePNGRepresentationOfImageToURLFormatColorSpaceOptionsError(m, $.NSURL.fileURLWithPath(outDir + '/' + nm.replace('.jpg', '.png')), $.kCIFormatL8, cs, $({}), null);
    n++;
  }
  return `${n} frames in ${(Date.now() - t0) / 1000}s`;
}
