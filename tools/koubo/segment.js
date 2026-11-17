ObjC.import('Foundation'); ObjC.import('Vision'); ObjC.import('CoreImage'); ObjC.import('AppKit');
function run(argv) {
  const [inPath, outPath] = argv;
  const t0 = Date.now();
  const url = $.NSURL.fileURLWithPath(inPath);
  const ci = $.CIImage.imageWithContentsOfURL(url);
  const W = ci.extent.size.width, H = ci.extent.size.height;
  const handler = $.VNImageRequestHandler.alloc.initWithCIImageOptions(ci, $({}));
  const req = $.VNGeneratePersonSegmentationRequest.alloc.init;
  req.qualityLevel = 0; // accurate
  req.outputPixelFormat = 1278226488; // kCVPixelFormatType_OneComponent8 'L008'
  const err = Ref();
  if (!handler.performRequestsError($([req]), err)) return 'perform failed';
  const obs = req.results.objectAtIndex(0);
  let m = $.CIImage.imageWithCVPixelBuffer(obs.pixelBuffer);
  const mw = m.extent.size.width, mh = m.extent.size.height;
  m = m.imageByApplyingTransform($.CGAffineTransformMakeScale(W / mw, H / mh));
  const ctx = $.CIContext.context;
  const cs = $.CGColorSpaceCreateDeviceGray();
  const ok = ctx.writePNGRepresentationOfImageToURLFormatColorSpaceOptionsError(m, $.NSURL.fileURLWithPath(outPath), $.kCIFormatL8, cs, $({}), null);
  return `mask ${mw}x${mh} -> ${W}x${H} ok=${ok} ${(Date.now()-t0)/1000}s`;
}
