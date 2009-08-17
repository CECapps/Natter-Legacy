<pre>
$Id$
<hr>original text:
<?php

error_reporting(E_ALL | E_STRICT);
ini_set('display_errors', true);

$demo_text  = 'How did you get here?';
$demo_text0 = 'ONE[b]TWO[/b]THREE';
$demo_text1 = 'This is [b]the[/b] [i]demo[/i] text.';
$demo_text2 = 'This is [b]the[/b] [color=red]demo[/color] text with a color.';
$demo_text3 = 'This is [b]the[/b] [color=red]demo[/color] text [i]with [u]mismatched[/i] nesting[/u]..';
$demo_text4 = '
NEXT: OPEN B
	[b] NEXT: OPEN I
		[i] NEXT: OPEN S
			[s] NEXT: OPEN U
				[u] NEXT: CLOSE B, CAUSING CLOSE U, S, I, CLOSE B, THEN OPEN I, S, U
				[/b]
			NEXT: CLOSE U
			[/u]
		NEXT: CLOSE I, CAUSING CLOSE S, CLOSE I, THEN OPEN S
	[/i]
NEXT: CLOSE S.
[/s]
THERE.';
$demo_text5 = 'What happens when there is an [i]un[b]closed[/i] tag?';

$demo_text99 = <<<DELIM
Hello [b]there[/b]!  [img]http://flare.solareclipse.net/biggrin.gif[/img] is a biggrin!!111on
And here's a right-aligned one:
[img:right]http://flare.solareclipse.net/biggrin.gif[/img]
And now a center that is also invalid.
[img:center]javascript:echo('http://flare.solareclipse.net/biggrin.gif')[/img]
[color:purple]Yup, right![/color]
eoneuno  [b]My na[me is [i]C[u]ha[s]r[/s]le[/u]s[/i][/b].
How are y]ou?  I'm doing fine.

Let's insert a table, for fun.

[literal]<table border=2 what=lol>
    <thead>
        <tr>
            <th>1</th>
            <th>2</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>3</td>
            <td>4</td>
        </tr>
    </tbody>
</table>[/literal]

How about an <cite>illegal tag</cite>?

My URL is [URL=http://solareclipse.net/]solareclipse.net[/url] (not [url]www.solareclipse.net[/url] or [url]www.[b]solareclipse[/b].net[/url])!

Does autolinking work?  www.google.com or maybe http://solareclipse.net/rofflesauce.html

My List is [list][*]One[*]Two[*]Three[/list] - isn't that grand?  Hey, can I do nested lists?

[list=1]
[*]First item
[*]Second item[list]
[*]First Nested Item
[*]Second Nested Item
[list=a][*]Hey, look, it's a third level nesting!
[*]And a second third level item.
[/list]
[*]Third nested item, on [email]charles@infopop.com[/email] the first nesting level
[*]And [color:red]number[/color] four
[list=I]
[*]Roman One, and does the [email=capps@solareclipse.net]alternate format[/email] for the email tag work?
[*]Roman Two
[list=i]
[*]roman one, here's a [url=http://domain.com/page name with spaces.html]URL with spaces[/url] to test.
[*]roman two
[*]roman three with a [email]bog+us@email address[/email]
[/list]
[*]Roman Three
[/list]
[/list]
[*]Third item, no nesting, but with a [url=http://domain.com/page.php?thing[]=1]URL with square brackets[/url] instead.
[/list]

Fantastic!!!111eleven  And now, ten blank newlines.










But how does it deal with an [b]unclosed bold tag?

[quote]Let's break the parse tree:[/quote]

[b]Bold open.[i]Ital open.[/b]Bold close - oops![/i]Ital closed.

And again inside code tags:

[code][b]Bold open.[i]Ital open.[/b]Bold close - oops![/i]Ital closed.

There were two newlines before this one.[/code]

And now, deep nesting.

0[quote]1[quote]2[quote]3[quote]4[quote]5[quote]6[quote]7[quote]8[quote]9[/quote]8[/quote]7[/quote]6[/quote]5[/quote]4[/quote]3[/quote]2[/quote]1[/quote]0

How about a [quote=Somebody]quote from Somebody?[/quote]

How are [quote=Some person or another]spaces handled in param names?[/quote]

What does my [quote=Name with post number,1234]post attribution[/quote] look like?

OKay, cool.  How about a [mr]tag now?[/mr]

Or maybe [fl]the fl tag[/fl] will work?

And finally, let's get fucked up.

[list=I][*]Roman One Again
[*]Roman Two Again
[*]OH SHIT A QUOTE [quote]ROFFLESAUCE[*]This should break shit WONDERFULLY[/quote] HAHAHAH
[*]And here's roman four.
[/list]

How about [sub]subscript[/sub] and [sup]superscript[/sup]?

End.
DELIM;


$actual_text = $demo_text99;

echo $actual_text;
echo '<hr>Parse:<br>';
$parser = new Natter_BBCode();
$parser->set($actual_text);
echo '<hr>renderBBCode:<br>';
echo $parser->renderBBCode();
echo '<hr>renderPlainText:<br>';
echo $parser->renderPlainText();
echo '<hr>renderHTML:<br>';
echo $parser->renderHTML();
echo '<hr>';





class Natter_BBCode {

	public $tags = array();
	private $tag_regex = '';
	private $body = '';
	private $nodes = array();
	private $tree = array();

/**
 * Constructor
 **/
	public function __construct() {
		$this->initTags();
		$this->reset();
	} // end __construct


/**
 * Initialize the tag list
 **/
	protected function initTags() {
		$this->tags['b'] = new Natter_BBCodeTagRenderer_B();
		$this->tags['i'] = new Natter_BBCodeTagRenderer_I();
		$this->tags['u'] = new Natter_BBCodeTagRenderer_U();
		$this->tags['s'] = new Natter_BBCodeTagRenderer_S();
		// $this->tags['color'] =
		$regex_stuff = array();
		foreach($this->tags as $tag => $j)
			$regex_stuff[] = '^(' . $tag . ')(?:[\=\:](.+?))?$';
		$this->tag_regex = join('|', $regex_stuff);
		$this->tags['BROKEN'] = new Natter_BBCodeTagRenderer_BrokenTag();
	} // end initTags


/**
 * Reset the body
 **/
	public function reset() {
		$this->body = '';
		$this->tree = array();
	} // end reset


/**
 * Set the body.
 * @param string $body
 **/
	public function set($body) {
		$this->reset();
		$this->body = $body;
		$this->parse();
	} // end set


/**
 * Add a tag
 * @param Natter_BBCodeTag $tag
 **/
	public function addTag(Natter_BBCodeTag $tag) {
	} // end addTag


/**
 * Get the object for a tag (to modify it)
 * @param string $tag Tag name
 * @return Natter_BBCodeTag
 **/
	public function getTag($tag) {
	} // end getTag


/**
 * Render the body to HTML
 * @return string
 **/
	public function renderHTML() {
		$children = $this->tree['__root__']['children'];
		$buffer = '';
		foreach($children as $child_id) {
			$buffer .= $this->tree[$child_id]['type'] == 'text'
							? $this->tree[$child_id]['body']
							: $this->tags[ $this->tree[$child_id]['tag'] ]->renderHTML($this, $this->tree, $child_id);
		} // end foreach
		return $buffer;
	} // end renderHTML


/**
 * Render the body to normalized BBCode
 * @return string
 **/
	public function renderBBCode() {
		$children = $this->tree['__root__']['children'];
		$buffer = '';
		foreach($children as $child_id) {
			$buffer .= $this->tree[$child_id]['type'] == 'text'
							? $this->tree[$child_id]['body']
							: $this->tags[ $this->tree[$child_id]['tag'] ]->renderBBCode($this, $this->tree, $child_id);
		} // end foreach
		return $buffer;
	} // end renderBBCode


/**
 * Render the body to plain text
 * @return string
 **/
	public function renderPlainText() {
		$children = $this->tree['__root__']['children'];
		$buffer = '';
		foreach($children as $child_id) {
			$buffer .= $this->tree[$child_id]['type'] == 'text'
							? $this->tree[$child_id]['body']
							: $this->tags[ $this->tree[$child_id]['tag'] ]->renderPlainText($this, $this->tree, $child_id);
		} // end foreach
		return $buffer;
	} // end renderPlainText


/**
 * Parse the body into a tree
 **/
	protected function parse() {
		$tagset = preg_split('/([\[\]])/', $this->body, null,  PREG_SPLIT_DELIM_CAPTURE );
		$total_chunks = count($tagset);
		$open_tags = array();

		for($i = 0; $i < $total_chunks; $i++) {
			$last_node_num = count($this->nodes);
		// What's our current chunk?
			$chunk = $tagset[$i];

		// If it looks like a tag opening, look for the close bracket.  It
		// should be the chunk after next.  Usually, at least.
			if($chunk == '[' && $tagset[$i + 2] == ']' && substr($tagset[$i + 1], 0, 1) != '/') {
			// This looks a tag open.  Is it?
				$matches = array();
				if(preg_match('~' . $this->tag_regex . '~', $tagset[$i + 1], $matches)) {
				// The parens could be anywhere inside the massive regex.
				// Pop off the global result and find the actual first match.
					array_shift($matches);
					while($matches[0] == '')
						array_shift($matches);
				// Stick the tag in the node list
					$this->nodes[] = array(
						'type' => 'tag',
						'tag' => $matches[0],
						'params' => isset($matches[1]) ? $matches[1] : null,
						'closer' => null,
					);
				// Place this opener at the top of the opener stack
					array_unshift($open_tags, array(
						'tag' => $matches[0],
						'id' =>  count($this->nodes) - 1
					));
				// We've processed the tag (+1) and the right bracket (+2),
				// skip to the next chunk.
					$i += 2;
					continue;
				} // end if
			// Okay, otherwise we failed to find a real tag open.  It's a text node.
				$this->nodes[] = array(
					'type' => 'text',
					'body' => $chunk
				);
			}

		// This looks like a tag close.
			elseif($chunk == '[' && $tagset[$i + 2] == ']' && substr($tagset[$i + 1], 0, 1) == '/') {
			// What's the tag we're closing?
				$tag_to_close = substr($tagset[$i + 1], 1);
			// If the user isn't an idiot, we should now be closing the tag
			// that we just opened a bit ago.  Are we lucky?
				if(isset($open_tags[0]) && $open_tags[0]['tag'] == $tag_to_close) {
				// Yup, we're lucky.
					$opener = array_shift($open_tags);
				// Close her up.
					$this->nodes[] = array(
						'type' => 'closetag',
						'tag' => $tag_to_close,
						'opener' => $opener['id'],
						'children' => array(),
					);
				// Tell the open tag that it has a closer.
					$this->nodes[ $opener['id'] ]['closer'] = count($this->nodes) - 1;
				// Skip along.
					$i += 2;
					continue;
				} // end if

			// Okay, if we got here, the most recently opened tag is still open.
			// That means that this closer isn't for the currently open tag.
			// Crap.
			// Look backwards through the open tag stack, looking for ourself.
				$opener_offset = null;
				foreach($open_tags as $id => $tag_info)
					if($tag_info['tag'] == $tag_to_close)
						$opener_offset = $id;
			// Did we even find the closer?
				if(is_null($opener_offset)) {
				// Nope.  This is a closer for a tag that was never opened.
				// As a result, we can't exactly close it, can we?
				// Stick the text chunks in the node list.
					$this->nodes[] = array(
						'type' => 'text',
						'body' => $chunk
					);
					continue;
				} // end if

			// Okay, we found out where we closed.  Before we close ourselves,
			// we need to close everything in between, then reopen them.
			// 1[i]2[b]3[/i]4[/b]5 -> 1[i]2[b]3[/b][/i][b]4[/b]5
			//          ^^^^  <- this ->       ^^^^^^^^^^^
			// 1 2 3 4       /2     /4 /3
			// 1 2 3 4 /4 /3 /2 3 4 /4 /3
				$new_open_tags = array();
				$working_offset = -1;
				while($opener = array_shift($open_tags)) {
					$working_offset++;
				// Close it up.
					$this->nodes[] = array(
						'type' => 'closetag',
						'tag'  => $opener['tag'],
						'opener' => $opener['id'],
					);
				// Tell the open tag that it has a closer.
					$this->nodes[ $opener['id'] ]['closer'] = count($this->nodes) - 1;
				// If we found ourselves, stop now.
					if($working_offset == $opener_offset)
						break;
				// Otherwise, shove this tag onto the list of tags to reopen.
					array_unshift($new_open_tags, $opener);
				} // end while
			// Now we need to re-open the tags...
				foreach($new_open_tags as $opener) {
				// Copy the original open tag, to get the params.
					$copy = $this->nodes[ $opener['id'] ];
					$copy['closer'] = null;
					$this->nodes[] = $copy;
				// The new open tag stack entry gets the new opener id
					$opener['id'] = count($this->nodes) - 1;
					array_unshift($open_tags, $opener);
				} // end foreach
			// Ugh, finally.  Okay, we just processed this tag, so we can
			// skip the tag name and close bracket.
				$i += 2;
				continue;
			}

		// Nope, it's a plain chunk of text.  How utterly mundane.
			else {
				$this->nodes[] = array(
					'type' => 'text',
					'body' => $chunk
				);
			} // end if
		} // end for

	// Quickly neuter unclosed tags.
		foreach($this->nodes as $node_id => $j)
			if($j['type'] == 'tag' && is_null($j['closer'])) {
				$this->nodes[$node_id]['unclosed_tag'] = $j['tag'];
				$this->nodes[$node_id]['tag'] = 'BROKEN';
			} // end if

	// We now have a list of opens, texts, and closes.  Let's turn it into
	// a nice happy tree.  Or rather, a virtual tree.  This is gonna be fun.
		$this->tree = array(
			'__root__' => array(
				'id' => '__root__',
				'type' => 'root',
				'children' => array()
			),
		);
		$parent_node =& $this->tree['__root__'];
		foreach($this->nodes as $node_id => $j) {
			$node =& $this->nodes[ $node_id ];
			$node['id'] = $node_id;
			$node['parent'] = $parent_node['id'];
		// If we really belong to our parents, attach ourself
			if($node['type'] == 'text' || $node['type'] == 'tag')
				$parent_node['children'][] = $node['id'];
		// If we're a tag, we become the next iteration's parent.
			if($node['type'] == 'tag')
				$parent_node =& $node;
		// If we're a close, our parent's parent becomes the next tag's parent.
			elseif($node['type'] == 'closetag')
				if(isset( $this->nodes[ $node['parent'] ] ) && isset( $this->nodes[ $this->nodes[ $node['parent'] ]['parent'] ] ))
					$parent_node =& $this->nodes[ $this->nodes[ $node['parent'] ]['parent'] ];
				else
					$parent_node =& $this->tree['__root__'];
		// If we get a bogus parent node, reset it to the root.
			if(!$parent_node)
				$parent_node =& $this->tree['__root__'];
		} // end foreach

	// Now that the nodes know their parentage, let's attach them to the tree.
		$child_list = $this->tree['__root__']['children'];
		while(count($child_list) > 0) {
		// Deal with the next child on the list
			$next_child = array_shift($child_list);
			if(!isset( $this->tree[ $next_child ] ))
				$this->tree[ $next_child ] = $this->nodes[ $next_child ];
		// If the child has children, stick them on the end.
			$new_children = isset($this->nodes[ $next_child ]['children']) ? $this->nodes[ $next_child ]['children'] : array();
			foreach($new_children as $new_child)
				$child_list[] = $new_child;
		// Now go through the total list of children and make sure that
		// we have copied them from the node list to the tree.
			foreach($child_list as $k => $child_id) {
				if(!isset( $this->tree[ $child_id ] )) {
					$this->tree[ $child_id ] = $this->nodes[ $child_id ];
				} // end if
			} // end foreach
		} // end while

	// Voila, we have a tree.
		// var_export($this->tree);
	} // end parse


} // end Natter_BBCode









class Natter_BBCodeTagRenderer_Simple {
	public $tag;
	public $can_have_params = false;
	public $multi_params = false;
	public $multi_param_sep = false;
	public $can_have_quoted_param = false;
	public $force_quoted_param = false;

	protected $html_open;
	protected $html_close;

	protected $param_callbacks = array();
	protected $render_html_callbacks = array();
	protected $render_bbcode_callbacks = array();
	protected $render_text_callbacks = array();


	function __construct($tag) {
		$this->tag = $tag;
	} // end __construct

	function renderHTML(Natter_BBCode &$bbcode, &$tree, $child_id) {
		$node = $tree[$child_id];
		$children = isset($node['children']) ? $node['children'] : array();
		$buffer = $this->html_open;
		foreach($children as $sub_child_id) {
			$buffer .= $tree[$sub_child_id]['type'] == 'text'
							? $tree[$sub_child_id]['body']
							: $bbcode->tags[ $tree[$sub_child_id]['tag'] ]->renderHTML($bbcode, $tree, $sub_child_id);
		} // end foreach
		return $buffer . $this->html_close;
	} // end renderHTML

	function renderBBCode(Natter_BBCode &$bbcode, &$tree, $child_id) {
		$node = $tree[$child_id];
		$children = isset($node['children']) ? $node['children'] : array();
		$buffer = '[' . $this->tag;
		if($this->can_have_params) {
			$buffer .= (($this->can_have_quoted_param || $this->force_quoted_param) ? '"' : '')
			         . $node['params']
					 . (($this->can_have_quoted_param || $this->force_quoted_param) ? '"' : '');
		} // end if
		$buffer .= ']';
		foreach($children as $sub_child_id) {
			$buffer .= $tree[$sub_child_id]['type'] == 'text'
							? $tree[$sub_child_id]['body']
							: $bbcode->tags[ $tree[$sub_child_id]['tag'] ]->renderBBCode($bbcode, $tree, $sub_child_id);
		} // end foreach
		return $buffer . '[/' . $this->tag . ']';
	} // end renderBBCode

	function renderPlainText(Natter_BBCode &$bbcode, &$tree, $child_id) {
		$node = $tree[$child_id];
		$children = isset($node['children']) ? $node['children'] : array();
		$buffer = '';
		foreach($children as $sub_child_id) {
			$buffer .= $tree[$sub_child_id]['type'] == 'text'
							? $tree[$sub_child_id]['body']
							: $bbcode->tags[ $tree[$sub_child_id]['tag'] ]->renderPlainText($bbcode, $tree, $sub_child_id);
		} // end foreach
		return $buffer;
	} // end renderPlainText

	function addParamCallback($callback) {}
	function addRenderCallback($render_mode, $callback) {}

}

class Natter_BBCodeTagRenderer_B extends Natter_BBCodeTagRenderer_Simple {
	public function __construct($tag = 'b') {
		parent::__construct($tag);
		$this->html_open = '<b>';
		$this->html_close = '</b>';
	} // end __construct
}

class Natter_BBCodeTagRenderer_S extends Natter_BBCodeTagRenderer_Simple {
	public function __construct($tag = 's') {
		parent::__construct($tag);
		$this->html_open = '<s>';
		$this->html_close = '</s>';
	} // end __construct
}

class Natter_BBCodeTagRenderer_I extends Natter_BBCodeTagRenderer_Simple {
	public function __construct($tag = 'i') {
		parent::__construct($tag);
		$this->html_open = '<i>';
		$this->html_close = '</i>';
	} // end __construct
}

class Natter_BBCodeTagRenderer_U extends Natter_BBCodeTagRenderer_Simple {
	public function __construct($tag = 'u') {
		parent::__construct($tag);
		$this->html_open = '<u>';
		$this->html_close = '</u>';
	} // end __construct
}


class Natter_BBCodeTagRenderer_BrokenTag extends Natter_BBCodeTagRenderer_Simple {
	public function __construct($tag = 'BROKEN') {
		parent::__construct($tag);
		$this->html_open = '';
		$this->html_close = '';
	} // end __construct

	function renderBBCode(Natter_BBCode &$bbcode, &$tree, $child_id) {
		$node = $tree[$child_id];
		$children = isset($node['children']) ? $node['children'] : array();
		$buffer = '';
		if(isset($node['unclosed_tag'])) {
			$buffer .= '[' . $node['unclosed_tag'];
			if($this->can_have_params) {
				$buffer .= (($this->can_have_quoted_param || $this->force_quoted_param) ? '"' : '')
						 . $node['params']
						 . (($this->can_have_quoted_param || $this->force_quoted_param) ? '"' : '');
			} // end if
		$buffer .= ']';
		} // end if
		foreach($children as $sub_child_id) {
			$buffer .= $tree[$sub_child_id]['type'] == 'text'
							? $tree[$sub_child_id]['body']
							: $bbcode->tags[ $tree[$sub_child_id]['tag'] ]->renderBBCode($bbcode, $tree, $sub_child_id);
		} // end foreach
		return $buffer;
	} // end renderBBCode

	function renderHTML(Natter_BBCode &$bbcode, &$tree, $child_id) {
		$node = $tree[$child_id];
		$children = isset($node['children']) ? $node['children'] : array();
		$buffer = isset($node['unclosed_tag']) ? '[' . $node['unclosed_tag'] . ']' : '';
		foreach($children as $sub_child_id) {
			$buffer .= $tree[$sub_child_id]['type'] == 'text'
							? $tree[$sub_child_id]['body']
							: $bbcode->tags[ $tree[$sub_child_id]['tag'] ]->renderHTML($bbcode, $tree, $sub_child_id);
		} // end foreach
		return $buffer;
	} // end renderHTML

}
