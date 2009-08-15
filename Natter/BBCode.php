<pre>
$Id$
text:
<hr />
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
$actual_text = $demo_text2;

$parser = new Natter_BBCode();
$parser->set($actual_text);
echo $parser->renderBBCode();






class Natter_BBCode {

	private $tags = array();
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
		$this->tags['b'] = new Natter_BBCodeTag('b', 0, null, null);
		$this->tags['i'] = new Natter_BBCodeTag('i', 0, null, null);
		$this->tags['u'] = new Natter_BBCodeTag('u', 0, null, null);
		$this->tags['s'] = new Natter_BBCodeTag('s', 0, null, null);
		$this->tags['color'] = new Natter_BBCodeTag('color', 1, null, null);
		$regex_stuff = array();
		foreach($this->tags as $tag)
			$regex_stuff[] = $tag->getOpenRegex();
		$this->tag_regex = join('|', $regex_stuff);
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
							: $this->tags[ $this->tree[$child_id]['tag'] ]->renderBBCode($this->tree, $child_id);
		} // end foreach
		return $buffer;
	} // end renderBBCode


/**
 * Render the body to plain text
 * @return string
 **/
	public function renderPlainText() {
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
				if($open_tags[0]['tag'] == $tag_to_close) {
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

	} // end parse


} // end Natter_BBCode






class Natter_BBCodeTag {

	public $tag = '';
	public $param_count = 0;
	public $param_quoted = null;
	public $param_separator = null;
	public $param_list = array();

	public function __construct($tag, $param_count, $param_quoted, $param_separator) {
		$this->tag = $tag;
		$this->param_count = $param_count;
		$this->param_quoted = $param_quoted;
		$this->param_separator = $param_separator;
	} // end __construct

	public function getOpenRegex() {
		return '^(' . $this->tag . ( $this->param_count ? ')=(.+?)' : ')' ) .'$';
	} // end getRegex

	public function getCloseRegex() {
		return '^/' . $this->tag . '$';
	} // end getRegex

	public function addParamCallback($callback) {
	} // end addParamCallback

	public function addRenderCallback($render_mode, $callback) {
	} // end addRenderCallback

	public function renderHTML() {
	} // end renderHTML

	public function renderBBCode(&$tree, $child_id) {
		$children = isset($tree[$child_id]['children']) ? $tree[$child_id]['children'] : array();
		$buffer = '[' . $this->tag;
		if($this->param_count) {
			$buffer .= '=';
			if($this->param_quoted)
				$buffer .= '"';
			if($this->param_count > 1)
				$buffer .= join($this->param_separator, $this->param_list);
			elseif($this->param_count == 1)
				$buffer .= $this->param_list[0];
			if($this->param_quoted)
				$buffer .= '"';
		} // end if
		$buffer .= ']';
		foreach($children as $sub_child_id) {
			$buffer .= $tree[$sub_child_id]['type'] == 'text'
							? $tree[$sub_child_id]['body']
							: $this->tags[ $tree[$sub_child_id]['tag'] ]->renderBBCode($sub_child_id);
		} // end foreach
		return $buffer . '[/' . $this->tag . ']';
	} // end renderBBCode

	public function renderPlainText() {
	} // end renderPlainText

} // end Natter_BBCodeTag

