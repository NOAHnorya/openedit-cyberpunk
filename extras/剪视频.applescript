-- 剪视频.app: opens Claude Code in this repo inside Terminal (macOS).
-- Double-click: a fresh session. Drop video files on the icon: a session that starts with those files.
-- __REPO__ below is a placeholder. Build from the repo root: first replace it with the repo path, then compile:
--   sed "s|__REPO__|$PWD|g" extras/剪视频.applescript > /tmp/剪视频.applescript
--   osacompile -o ~/Desktop/剪视频.app /tmp/剪视频.applescript

on run
	openClaude("")
end run

on open droppedItems
	set fileList to ""
	repeat with f in droppedItems
		set fileList to fileList & linefeed & "- " & POSIX path of f
	end repeat
	openClaude("我要处理这些视频：" & fileList & linefeed & "先看一下素材，再问我想怎么剪。")
end open

on openClaude(firstPrompt)
	set cmd to "cd " & quoted form of "__REPO__" & " && claude"
	if firstPrompt is not "" then set cmd to cmd & " " & quoted form of firstPrompt
	set wasRunning to application "Terminal" is running
	tell application "Terminal"
		if wasRunning then
			do script cmd
		else
			-- A cold start opens its own default window; use it rather than leaving an empty second one.
			activate
			repeat 50 times
				if (count of windows) > 0 then exit repeat
				delay 0.1
			end repeat
			do script cmd in front window
		end if
		activate
	end tell
end openClaude
