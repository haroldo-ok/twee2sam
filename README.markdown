README : twee2sam
======

This tool is intended to convert [Twee] projects (that you can export from [Twine]) into [SAM] projects. With it, it's possible to create Sega Master System adventure games using Twine.

Currently, it supports a subset of the Twine commands; so far, only links and images are supported.

You can see a working example at example/simple; run Compile.bat to make it run.


Compiled version
----------------

You can get a compiled version from https://dl.dropboxusercontent.com/u/1235428/sms/twee2sam-2015-01-05a.rar

Of from the [SMSPower thread](http://www.smspower.org/forums/viewtopic.php?t=14568)


Image support
-------------

The images must be in the png format, have a resolution of 256x144, and can't have more than 16 colors. Be careful to not use an exceedingly detailed image, as SAM can't display images with more than 320 tiles. 

Commands
========

[img[imagename.png]]
--------------------

Displays an image

&lt;&lt;pause&gt;&gt;
---------

Forces a page break or, if there's no text, just waits for the user to press any button.

&lt;&lt;set *variable* to *expression*&gt;&gt;
---------

Sets the value of a variable to the value of the expression.

Examples:

&lt;&lt;set *variable1* = 42 &gt;&gt;

&lt;&lt;set *variable1* = *variable2* &gt;&gt;

&lt;&lt;set *variable1* = 42 - 24 &gt;&gt;

&lt;&lt;set *variable1* = *variable1* + *variable2* &gt;&gt;

In general terms, the basic Twine math operations (+, -, /, * ) are supported in the form:

target = operand1 operator operand2

Either or both of the operands can be variables. Compound operations (in parenthesis) are not supported.

&lt;&lt;print *variable* &gt;&gt;
---------

Outputs the value of the given variable in a text passage.

&lt;&lt;if *expression*&gt;&gt;...&lt;&lt;endif&gt;&gt;
---------

Conditionally executes the code between &lt;&lt;if &gt;&gt; and &lt;&lt;endif&gt;&gt; if the *expression* evaluates to *true*.

Examples:

&lt;&lt;if *variable1* is True &gt;&gt;...&lt;&lt;endif&gt;&gt;

&lt;&lt;if *variable1* gt 99 &gt;&gt;...&lt;&lt;endif&gt;&gt;

&lt;&lt;if *variable1* lt *variable2* &gt;&gt;...&lt;&lt;endif&gt;&gt;

Note: &lt;&lt;else&gt;&gt; is not implemented yet.

&lt;&lt;call *passage* &gt;&gt;
---------

Calls a passage of text - this is effectively how twee2sam converts the Twine passages into a link story, however it can also be used to call out to specific subroutines.

Examples:

&lt;&lt;call inventory_passage &gt;&gt;

A *call* is most often used to jump to another text passage, once you have finished with the 'subroutine' passage, you can return back to the original position with the *return* command:

Example:

&lt;&lt;return&gt;&gt;

The two above commands allow you to have 'subroutines' unconnected from your main Twine story which can be called from anywhere without using the traditional [[link]] syntax and then return back to the previous position - this would normally require the subroutine to know which passage to return back to, which does not work easily with subroutines that may be called from many different locations (high score screens, inventory/player status, a pause menu etc).

&lt;&lt;music *"filename.epsgmod"*&gt;&gt;
---------

Plays music in *.epsgmod* format, as exported by [Mod2PSG2]

Expressions
-----------

Currently, twee2sam has only limited expression support:

- **true** evaluates to true;
- **false** evaluates to false;
- ***variable name*** evaluates to the current value of the variable;
- **not** ***variable_name*** or ***!variable_name*** evaluates to the logical negation of the current value of the variable; that is, if 'variable' is true, '!variable' is false, and vice versa.
- **gt** evaluates to true if the left side (target) is greater than the right. Note: **not** is not supported with this operator.
- **lt** evaluates to true if the left side (target) is less than the right. Note: **not** is not supported with this operator.

So, essentially, the tool currently supports single boolean constants or single variables, with or without negation and less than (lt) or greater than (gt) and equivalence (=) comparisons. Future versions will support more complex expressions.

Note that all variables are referenced with a leading $, as per normal Twine syntax.

History
=======

2015-01-04: Added print, basic math functions and gt, and lt operators. Added external tiddlywiki source files.

2014-02-19: Updated SAM to use PS Gaiden compression.

2014-02-17: Corrected word wrapping bug.

2014-02-01: Implemented the &lt;&lt;set&gt;&gt; and &lt;&lt;if&gt;&gt; commands.

2014-01-30: Implemented text buffer overflow checking and also implemented the &lt;&lt;pause&gt;&gt; command.

2014-01-27: Generated a compiled exe version of twee2sam.py, so that people can use the tool without having Python installed.

2014-01-26: Implemented image displaying support.

2014-01-23: First working version. Links are supported.




[twee]: https://github.com/tweecode/twee "Twee story engine"
[twine]: https://github.com/tweecode/twine "A visual tool for creating interactive stories for the Web"
[SAM]: http://www.haroldo-ok.com/sam-simple-adventure-maker-sms/ "SAM - Simple Adventure Maker"
[Python]: http://www.python.org/ "Python Programming Language"
[Mod2PSG2]: http://www.smspower.org/Music/Mod2PSG2 "A tracker for the Sega Master System's sound chip"
